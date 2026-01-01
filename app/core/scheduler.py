# app/core/scheduler.py

"""
Background scheduler for automated tasks.

This module sets up APScheduler to run periodic tasks:
- Daily cleanup of past activity availability records
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.activity_availability import ActivityAvailabilityService


def cleanup_past_availability():
    """
    Scheduled job to clean up past activity availability records.
    Runs daily at 2:00 AM server time.
    """
    db: Session = SessionLocal()
    try:
        result = ActivityAvailabilityService.cleanup_past_closures(db)
        print(f"[SCHEDULER] Availability cleanup: {result['message']}")
    except Exception as e:
        print(f"[SCHEDULER] Error during availability cleanup: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Initialize and start the background scheduler.
    Call this from your main application startup.
    """
    scheduler = AsyncIOScheduler()

    # Schedule daily cleanup at 2:00 AM
    scheduler.add_job(
        cleanup_past_availability,
        CronTrigger(hour=2, minute=0),  # 2:00 AM daily
        id="cleanup_past_availability",
        name="Clean up past activity availability records",
        replace_existing=True,
    )

    scheduler.start()
    print("[SCHEDULER] Background scheduler started")

    return scheduler
