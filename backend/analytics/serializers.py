from rest_framework import serializers
from .models import AnalysisJob, AnalysisResult


class AnalysisJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisJob
        fields = [
            'job_id',
            'employee_id',
            'week_start',
            'daily_hours',
            'hourly_rate',
            'status',
            'created_at'
        ]
        read_only_fields = ['job_id', 'status', 'created_at']

    def validate_daily_hours(self, value):
        if not isinstance(value, list) or len(value) != 7:
            raise serializers.ValidationError(
                "daily_hours must be a list of exactly 7 numbers (Mon-Sun)."
            )

        for hours in value:
            if not isinstance(hours, (int, float)):
                raise serializers.ValidationError(
                    "All elements in daily_hours must be numbers."
                )
            if hours < 0 or hours > 24:
                raise serializers.ValidationError(
                    "Daily hours must be between 0 and 24."
                )

        return value

    def validate_hourly_rate(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Hourly rate must be greater than 0."
            )
        return value


class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = [
            'total_hours',
            'overtime_hours',
            'risk_level',
            'compliance_status',
            'public_holidays_in_week',
            'recommendation',
            'error_message',
        ]


# 🔥 Optional: Clean Combined Response Serializer
class JobStatusSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()
    result = AnalysisResultSerializer(required=False)