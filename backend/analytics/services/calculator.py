from datetime import datetime, timedelta
from decimal import Decimal


def calculate_totals(daily_hours):
    """
    Calculates total and overtime hours.
    Returns (total_hours, overtime_hours)
    """
    if not daily_hours:
        return Decimal("0.00"), Decimal("0.00")

    total_hours = sum(Decimal(str(h)) for h in daily_hours)
    overtime_hours = max(total_hours - Decimal("40"), Decimal("0"))

    return total_hours, overtime_hours


def get_risk_level(total_hours):
    """
    Categorizes risk based on total weekly hours.
    """
    total_hours = Decimal(str(total_hours))

    if total_hours <= Decimal("40"):
        return "LOW"
    elif total_hours <= Decimal("48"):
        return "MEDIUM"
    else:
        return "HIGH"


def get_compliance_status(total_hours):
    """
    Determines compliance based on EU working time directive (48-hour rule).
    """
    total_hours = Decimal(str(total_hours))

    if total_hours <= Decimal("48"):
        return "OK"
    else:
        return "VIOLATION"


def count_holidays_in_week(week_start_date, holidays_list):
    """
    Counts public holidays within the 7-day week.
    """
    if not holidays_list:
        return 0

    if isinstance(week_start_date, str):
        week_start_date = datetime.strptime(week_start_date, "%Y-%m-%d").date()

    week_end_date = week_start_date + timedelta(days=6)

    count = 0

    for holiday in holidays_list:
        try:
            holiday_date = datetime.strptime(
                holiday["date"], "%Y-%m-%d"
            ).date()

            if week_start_date <= holiday_date <= week_end_date:
                count += 1
        except Exception:
            continue  # skip malformed entries

    return count


def generate_recommendation(risk_level, compliance_status):
    """
    Generates recommendation text based on workforce risk & compliance.
    """
    if compliance_status == "VIOLATION":
        return (
            "CRITICAL FLAG: Employee exceeds maximum 48-hour "
            "working limit. Reduce hours immediately."
        )

    if risk_level == "HIGH":
        return (
            "Warning: High risk level detected. Monitor fatigue "
            "and redistribute workload if necessary."
        )

    if risk_level == "MEDIUM":
        return (
            "Notice: Overtime accumulation detected. Continue "
            "monitoring to prevent burnout."
        )

    return "Operations normal. Workforce capacity is balanced."