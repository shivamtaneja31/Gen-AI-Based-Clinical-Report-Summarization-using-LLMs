import asyncio
import logging
from celery import Task
from typing import Dict, Optional, Any

from app.domain.models import ReportType, ReportStatus
from app.services.summarization import summarization_service
from app.services.storage import db_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base class for async tasks that use asyncio"""
    
    def _run_async(self, coro):
        """Run an async coroutine"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


@celery_app.task(bind=True, base=AsyncTask, name="summarize_report", max_retries=3)
def summarize_report(self, report_id: str, report_type: str):
    """Task to summarize a clinical report"""
    logger.info(f"Starting summarization task for report {report_id}")
    
    try:
        # Convert string to enum
        report_type_enum = ReportType(report_type)
        
        # Run the summarization
        summary = self._run_async(
            summarization_service.summarize_report(
                report_id=report_id,
                report_type=report_type_enum
            )
        )
        
        if summary:
            logger.info(f"Successfully summarized report {report_id}")
            return {
                "success": True,
                "report_id": report_id,
                "summary_id": summary.id
            }
        else:
            logger.error(f"Failed to summarize report {report_id}")
            return {
                "success": False,
                "report_id": report_id,
                "error": "Failed to generate summary"
            }
            
    except Exception as e:
        logger.error(f"Error in summarize_report task for {report_id}: {e}")
        # Update report status to failed
        self._run_async(
            db_service.update_report_status(report_id, ReportStatus.FAILED)
        )
        # Retry after exponential backoff
        self.retry(exc=e, countdown=2 ** self.request.retries * 60)


@celery_app.task(bind=True, base=AsyncTask, name="batch_process_reports")
def batch_process_reports(self, batch_size: int = 10):
    """Task to process a batch of pending reports"""
    logger.info(f"Starting batch processing task for up to {batch_size} reports")
    
    try:
        self._run_async(
            summarization_service.batch_process_pending_reports(batch_size=batch_size)
        )
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error in batch_process_reports task: {e}")
        return {"success": False, "error": str(e)}


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks"""
    # Process pending reports every 5 minutes
    sender.add_periodic_task(
        300.0,
        batch_process_reports.s(batch_size=20),
        name="process-pending-reports-every-5-minutes"
    )