from django.test import TestCase
from analytics.services.calculator import (
    calculate_totals,
    get_risk_level,
    get_compliance_status
)


class CoreLogicTests(TestCase):

    def test_total_hours_normal(self):
        total, overtime = calculate_totals([8, 8, 8, 8, 8, 0, 0])
        self.assertEqual(total, 40)
        self.assertEqual(overtime, 0)

    def test_total_hours_overtime(self):
        total, overtime = calculate_totals([10, 10, 10, 10, 10, 0, 0])
        self.assertEqual(total, 50)
        self.assertEqual(overtime, 10)

    def test_risk_levels(self):
        self.assertEqual(get_risk_level(30), "LOW")
        self.assertEqual(get_risk_level(45), "MEDIUM")
        self.assertEqual(get_risk_level(50), "HIGH")

    def test_compliance_status(self):
        self.assertEqual(get_compliance_status(48), "OK")
        self.assertEqual(get_compliance_status(49), "VIOLATION")