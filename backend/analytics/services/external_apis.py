import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ExternalAPIService:
    def __init__(self):
        self.pay_api_url = settings.FRIEND_PAY_API_URL
        self.holiday_api_url = settings.PUBLIC_HOLIDAY_API_URL
        self.timeout = 10 # 10 seconds timeout
        self.is_mock_pay = not self.pay_api_url or 'example' in self.pay_api_url

    def get_estimated_pay(self, total_hours, hourly_rate):
        """Calls the serverless AWS Lambda endpoint to calculate pay."""
        if self.is_mock_pay:
            logger.info("[MOCK PAY API] Faking Friend Pay API Request")
            return float(total_hours) * float(hourly_rate)

        payload = {
            "total_hours": float(total_hours),
            "hourly_rate": float(hourly_rate)
        }
        try:
            response = requests.post(self.pay_api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return float(data.get('estimated_pay', 0))
        except requests.exceptions.Timeout:
            logger.error("Timeout occurred while calling the Pay API.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Pay API: {e}")
            return None

    def get_public_holidays(self, year, country_code="IE"):
        """Fetches public holidays for a given year and country (Default: Ireland IE)."""
        if not self.holiday_api_url:
            return []

        url = f"{self.holiday_api_url.rstrip('/')}/{year}/{country_code}"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Timeout occurred while calling the Holiday API.")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Holiday API: {e}")
            return []

external_apis = ExternalAPIService()
