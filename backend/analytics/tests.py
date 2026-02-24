import unittest
from django.test import TestCase
from unittest.mock import patch
from .services.calculator import calculate_totals, get_risk_level, get_compliance_status, count_holidays_in_week
from .services.external_apis import external_apis

class CoreCalculatorTests(unittest.TestCase):
    
    def test_calculate_totals_normal(self):
        hours = [8, 8, 8, 8, 8, 0, 0] # 40 h
        total, overtime = calculate_totals(hours)
        self.assertEqual(total, 40)
        self.assertEqual(overtime, 0)
        
    def test_calculate_totals_overtime(self):
        hours = [10, 10, 10, 10, 10, 0, 0] # 50 h
        total, overtime = calculate_totals(hours)
        self.assertEqual(total, 50)
        self.assertEqual(overtime, 10)

    def test_risk_level_classifications(self):
        self.assertEqual(get_risk_level(30), 'LOW')
        self.assertEqual(get_risk_level(40), 'LOW')
        self.assertEqual(get_risk_level(41), 'MEDIUM')
        self.assertEqual(get_risk_level(48), 'MEDIUM')
        self.assertEqual(get_risk_level(49), 'HIGH')
        
    def test_compliance_status(self):
        self.assertEqual(get_compliance_status(48), 'OK')
        self.assertEqual(get_compliance_status(49), 'VIOLATION')

    def test_count_holidays_in_week(self):
        # A week passing through christmas week
        week_start = '2023-12-25' 
        fake_api_holidays = [
             {'date': '2023-12-25', 'name': 'Christmas Day'},
             {'date': '2023-12-26', 'name': 'St. Stephens Day'},
             {'date': '2024-01-01', 'name': 'New Years Day'}
        ]
        
        count = count_holidays_in_week(week_start, fake_api_holidays)
        self.assertEqual(count, 2)

class ExternalServicesTests(unittest.TestCase):
    
    @patch('analytics.services.external_apis.requests.post')
    def test_pay_api_success(self, mock_post):
        mock_post.return_value.json.return_value = {"estimated_pay": 750.50}
        mock_post.return_value.status_code = 200
        
        # Override mock mode for test
        original_mock_state = external_apis.is_mock_pay
        external_apis.is_mock_pay = False
        external_apis.pay_api_url = "http://fake-url.com"
        
        pay = external_apis.get_estimated_pay(50, 15.01)
        self.assertEqual(pay, 750.50)
        
        # Restore state
        external_apis.is_mock_pay = original_mock_state

    @patch('analytics.services.external_apis.requests.post')
    def test_pay_api_timeout_fallback(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        original_mock_state = external_apis.is_mock_pay
        external_apis.is_mock_pay = False
        external_apis.pay_api_url = "http://fake-url.com"
        
        pay = external_apis.get_estimated_pay(50, 15)
        self.assertIsNone(pay)
        
        external_apis.is_mock_pay = original_mock_state
