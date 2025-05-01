from celery import Celery
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "clinical_report_summarizer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Import tasks to ensure they're registered
from app.tasks import summarization_tasks