from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Avg

from .models import AnalysisJob, AnalysisResult
from .serializers import AnalysisJobSerializer, AnalysisResultSerializer
from .services.sqs_client import sqs_client

import logging

logger = logging.getLogger(__name__)


# ==========================
# AUTH & FRONTEND VIEWS
# ==========================

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True


class InputPageView(LoginRequiredMixin, TemplateView):
    template_name = "input.html"
    login_url = "/login/"


class ReportPageView(LoginRequiredMixin, TemplateView):
    template_name = "report.html"
    login_url = "/login/"


class HistoryView(LoginRequiredMixin, TemplateView):
    template_name = "history.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = AnalysisJob.objects.filter(
            user=self.request.user
        ).order_by('-week_start').select_related('result')
        context['jobs'] = jobs
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_staff:
            jobs_qs = AnalysisJob.objects.all()
            results_qs = AnalysisResult.objects.all()
        else:
            jobs_qs = AnalysisJob.objects.filter(user=user)
            results_qs = AnalysisResult.objects.filter(job__user=user)

        user_jobs_qs = jobs_qs

        available_weeks = [
            str(d) for d in
            user_jobs_qs
            .values_list('week_start', flat=True)
            .distinct()
            .order_by('-week_start')
        ]

        context['available_weeks'] = available_weeks

        selected_week = self.request.GET.get('week', '')
        context['selected_week'] = selected_week

        if selected_week:
            jobs_qs = jobs_qs.filter(week_start=selected_week)
            results_qs = results_qs.filter(job__week_start=selected_week)

        context['total_jobs'] = jobs_qs.count()
        context['completed_jobs'] = jobs_qs.filter(status='completed').count()
        context['high_risk_cases'] = results_qs.filter(risk_level='HIGH').count()
        context['compliance_violations'] = results_qs.filter(
            compliance_status='VIOLATION'
        ).count()

        avg_hours = results_qs.aggregate(
            Avg('total_hours')
        )['total_hours__avg']

        context['avg_weekly_hours'] = round(float(avg_hours), 1) if avg_hours else 0

        return context


# ==========================
# INLINE MOCK PROCESSOR
# ==========================

def _process_job_inline(job):
    from .services.calculator import (
        calculate_totals,
        get_risk_level,
        get_compliance_status,
        count_holidays_in_week,
        generate_recommendation,
    )
    from .services.external_apis import external_apis

    daily_hours = job.daily_hours
    hourly_rate = float(job.hourly_rate)
    week_start_str = str(job.week_start)

    total_hours, overtime_hours = calculate_totals(daily_hours)
    risk_level = get_risk_level(total_hours)
    compliance_status = get_compliance_status(total_hours)

    estimated_pay = external_apis.get_estimated_pay(
        total_hours,
        hourly_rate
    )

    year = week_start_str.split("-")[0]
    holidays_list = external_apis.get_public_holidays(year, "IE")

    holidays_count = 0
    if holidays_list:
        holidays_count = count_holidays_in_week(
            week_start_str,
            holidays_list
        )

    recommendation = generate_recommendation(
        risk_level,
        compliance_status
    )

    AnalysisResult.objects.create(
        job=job,
        total_hours=total_hours,
        overtime_hours=overtime_hours,
        risk_level=risk_level,
        compliance_status=compliance_status,
        estimated_pay=estimated_pay,
        public_holidays_in_week=holidays_count,
        recommendation=recommendation,
    )

    job.status = "completed"
    job.save()

    logger.info(f"[MOCK] Inline processed job {job.job_id}")


# ==========================
# PUBLIC API ENDPOINTS
# ==========================

class AnalyseRequestView(APIView):
    """
    POST /api/v1/workforce/analyse-request
    Public endpoint for friend integration.
    """
    permission_classes = [AllowAny]

    def post(self, request):

        serializer = AnalysisJobSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save job safely
        if request.user.is_authenticated:
            job = serializer.save(
                status="processing",
                user=request.user
            )
        else:
            job = serializer.save(status="processing")

        try:
            sqs_client.send_job(
                job_id=str(job.job_id),
                employee_id=job.employee_id,
                week_start=str(job.week_start),
                daily_hours=job.daily_hours,
                hourly_rate=float(job.hourly_rate),
            )
        except Exception as e:
            job.status = "failed"
            job.save()
            return Response(
                {"job_id": str(job.job_id), "status": "failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Mock inline processing (local development)
        if sqs_client.is_mock:
            try:
                _process_job_inline(job)
            except Exception as e:
                AnalysisResult.objects.get_or_create(
                    job=job,
                    defaults={"error_message": str(e)}
                )
                job.status = "failed"
                job.save()

        job.refresh_from_db()

        return Response(
            {
                "job_id": str(job.job_id),
                "status": job.status
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AnalyseResultView(APIView):
    """
    GET /api/v1/workforce/analyse-result?job_id=...
    Public result retrieval endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):

        job_id = request.query_params.get("job_id")

        if not job_id:
            return Response(
                {"error": "job_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = get_object_or_404(AnalysisJob, job_id=job_id)

        # If authenticated user → enforce ownership
        if request.user.is_authenticated:
            if not request.user.is_staff and job.user != request.user:
                return Response(
                    {"error": "You do not have permission."},
                    status=status.HTTP_403_FORBIDDEN
                )

        if job.status == "processing":
            return Response({
                "job_id": str(job.job_id),
                "status": "processing"
            })

        if job.status == "failed":
            error_msg = "Job processing failed."
            if hasattr(job, "result") and job.result.error_message:
                error_msg = job.result.error_message

            return Response({
                "job_id": str(job.job_id),
                "status": "failed",
                "error": error_msg
            })

        if job.status == "completed":
            serializer = AnalysisResultSerializer(job.result)
            return Response({
                "job_id": str(job.job_id),
                "status": "completed",
                "result": serializer.data
            })

        return Response(
            {"error": "Unknown job status"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )