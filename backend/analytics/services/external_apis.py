import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class ExternalAPIService:
    def __init__(self):
        self.pay_api_url = getattr(settings, "FRIEND_PAY_API_URL", None)
        self.holiday_api_url = getattr(settings, "PUBLIC_HOLIDAY_API_URL", None)
        self.timeout = 10  # seconds

    # ==========================================================
    # FRIEND PAYROLL API CALL
    # ==========================================================
    def get_payroll_data(
        self,
        employee_id,
        employee_name,
        hourly_rate,
        total_hours,
        standard_hours_limit=40,
        overtime_multiplier=1.5
    ):
        """
        Calls external Payroll Lambda API and returns gross_pay.
        """

        if not self.pay_api_url:
            print("❌ FRIEND_PAY_API_URL not configured in settings.")
            return None

        payload = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "hourly_rate": float(hourly_rate),
            "total_hours": float(total_hours),
            "standard_hours_limit": standard_hours_limit,
            "overtime_multiplier": overtime_multiplier
        }

        try:
            # 🔥 DEBUG PRINTS (VERY IMPORTANT)
            print("\n=== PAYROLL FUNCTION CALLED ===")
            print("URL:", self.pay_api_url)
            print("Payload:", payload)

            response = requests.post(
                self.pay_api_url,
                json=payload,
                timeout=self.timeout
            )

            print("Status Code:", response.status_code)
            print("Response Text:", response.text)

            response.raise_for_status()

            data = response.json()

            if data.get("success"):
                gross_pay = data.get("data", {}).get("gross_pay")
                print("✅ Gross Pay Received:", gross_pay)
                return float(gross_pay) if gross_pay is not None else None

            print("❌ Payroll API returned success=False.")
            return None

        except requests.exceptions.Timeout:
            print("❌ Payroll API request timed out.")
            return None

        except requests.exceptions.RequestException as e:
            print("❌ Payroll API request failed:", str(e))
            return None

        except Exception as e:
            print("❌ Unexpected Payroll API error:", str(e))
            return None

    # ==========================================================
    # PUBLIC HOLIDAY API CALL
    # ==========================================================
    def get_public_holidays(self, year, country_code="IE"):

        if not self.holiday_api_url:
            print("❌ PUBLIC_HOLIDAY_API_URL not configured.")
            return []

        url = f"{self.holiday_api_url.rstrip('/')}/{year}/{country_code}"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            print("❌ Holiday API request timed out.")
            return []

        except requests.exceptions.RequestException as e:
            print("❌ Holiday API request failed:", str(e))
            return []

        except Exception as e:
            print("❌ Unexpected Holiday API error:", str(e))
            return []


# Singleton instance
external_apis = ExternalAPIService()