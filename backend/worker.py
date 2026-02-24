from decimal import Decimal


def process_job(payload):
    """Executes calculation chain and API integrations."""
    job_id = payload.get("job_id")
    logger.info(f"Processing Job: {job_id}")

    try:
        job = AnalysisJob.objects.get(job_id=job_id)
    except AnalysisJob.DoesNotExist:
        logger.error(f"Job {job_id} not found in DB. Skipping.")
        return

    try:
        # Normalize inputs
        daily_hours = payload["daily_hours"]
        hourly_rate = Decimal(str(payload["hourly_rate"]))
        week_start_str = payload["week_start"]

        # 1️⃣ Core Calculations
        total_hours, overtime_hours = calculate_totals(daily_hours)
        risk_level = get_risk_level(total_hours)
        compliance_status = get_compliance_status(total_hours)

        # 2️⃣ Pay API
        try:
            estimated_pay = external_apis.get_estimated_pay(
                total_hours, hourly_rate
            )
        except Exception as e:
            logger.warning(f"Pay API failed: {e}")
            estimated_pay = None

        # 3️⃣ Public Holiday API
        try:
            year = week_start_str.split("-")[0]
            holidays_list = external_apis.get_public_holidays(year, "IE")
            holidays_count = (
                count_holidays_in_week(week_start_str, holidays_list)
                if holidays_list else 0
            )
        except Exception as e:
            logger.warning(f"Holiday API failed: {e}")
            holidays_count = 0

        # 4️⃣ Recommendation
        recommendation = generate_recommendation(
            risk_level, compliance_status
        )

        # 5️⃣ Save or update result safely
        AnalysisResult.objects.update_or_create(
            job=job,
            defaults={
                "total_hours": total_hours,
                "overtime_hours": overtime_hours,
                "risk_level": risk_level,
                "compliance_status": compliance_status,
                "estimated_pay": estimated_pay,
                "public_holidays_in_week": holidays_count,
                "recommendation": recommendation,
                "error_message": None,
            },
        )

        job.status = "completed"
        job.save()

        logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        logger.error(traceback.format_exc())

        AnalysisResult.objects.update_or_create(
            job=job,
            defaults={"error_message": str(e)},
        )

        job.status = "failed"
        job.save()