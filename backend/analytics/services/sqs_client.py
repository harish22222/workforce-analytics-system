import boto3
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SQSClient:
    def __init__(self):
        self.queue_url = getattr(settings, 'SQS_QUEUE_URL', None)
        self.region = getattr(settings, 'AWS_REGION', 'us-east-1')
        self.is_mock = False
        
        # Simple safeguard for local development if sqs isn't accessible
        aws_key = getattr(settings, 'AWS_ACCESS_KEY_ID', 'test')
        if not self.queue_url or 'test' in aws_key:
            self.is_mock = True
            logger.warning("AWS Credentials or SQS Queue URL not loaded correctly, falling back to Mock SQS.")
        else:
            self.sqs = boto3.client('sqs', region_name=self.region)

    def send_job(self, job_id, employee_id, week_start, daily_hours, hourly_rate):
        """Sends job payload to SQS."""
        payload = {
            'job_id': str(job_id),
            'employee_id': employee_id,
            'week_start': str(week_start),
            'daily_hours': daily_hours,
            'hourly_rate': str(hourly_rate)
        }
        
        if self.is_mock:
            # We bypass real AWS calls if mock
            logger.info(f"[MOCK SQS] Sent Message: {payload}")
            return {'MessageId': 'mock-sqs-message-id'}
            
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(payload),
                MessageGroupId="workforce-analytics", # In case it's a FIFO queue
                MessageDeduplicationId=str(job_id)
            )
            return response
        except Exception as e:
            logger.error(f"Error sending message to SQS: {e}")
            raise

sqs_client = SQSClient()
