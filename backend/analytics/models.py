import uuid
from django.db import models
from django.contrib.auth.models import User


class AnalysisJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="jobs")
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    job_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    employee_id = models.CharField(max_length=100)
    week_start = models.DateField()
    daily_hours = models.JSONField(
        help_text="List of 7 numbers representing hours worked (Mon-Sun)"
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job {self.job_id} - {self.employee_id} ({self.status})"


class AnalysisResult(models.Model):
    RISK_CHOICES = [
        ('LOW', 'LOW'),
        ('MEDIUM', 'MEDIUM'),
        ('HIGH', 'HIGH'),
    ]

    COMPLIANCE_CHOICES = [
        ('OK', 'OK'),
        ('VIOLATION', 'VIOLATION'),
    ]

    job = models.OneToOneField(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='result'
    )

    total_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        null=True,
        blank=True
    )

    compliance_status = models.CharField(
        max_length=20,
        choices=COMPLIANCE_CHOICES,
        null=True,
        blank=True
    )

    estimated_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    public_holidays_in_week = models.IntegerField(default=0)

    recommendation = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for Job {self.job.job_id}"