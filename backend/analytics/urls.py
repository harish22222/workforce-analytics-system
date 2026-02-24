from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    AnalyseRequestView, AnalyseResultView,
    InputPageView, ReportPageView, DashboardView, CustomLoginView, HistoryView
)

urlpatterns = [
    # Auth views
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Frontend views
    path('', DashboardView.as_view(), name='dashboard'),
    path('input/', InputPageView.as_view(), name='input-page'),
    path('report', ReportPageView.as_view(), name='report-page'),
    path('history/', HistoryView.as_view(), name='history'),
    
    # API endpoints
    path('api/v1/workforce/analyse-request', AnalyseRequestView.as_view(), name='analyse-request'),
    path('api/v1/workforce/analyse-result', AnalyseResultView.as_view(), name='analyse-result'),
]
