import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any

import aiokafka
import json

from app.core.config import settings
from app.domain.ai_summary import AISummaryGenerator, ReportType, Summary
from app.domain.models import ReportStatus
from app.services.data_ingestion import data_ingestion_service
from app.services.storage import db_service

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for report summarization"""
    
    def __init__(self):
        self.ai_generator = AISummaryGenerator()
        self.producer = None
    
    async def init_kafka_producer(self):
        """Initialize the Kafka producer"""
        if self.producer is None:
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )
            await self.producer.start()
            logger.info("Kafka producer initialized")
    
    async def close_kafka_producer(self):
        """Close the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer closed")
    
    async def summarize_report(self, report_id: str, report_type: ReportType) -> Optional[Summary]:
        """Generate a summary for a report"""
        try:
            # Update report status to processing
            await db_service.update_report_status(report_id, ReportStatus.PROCESSING)
            
            # Get the report from S3
            report = await data_ingestion_service.get_report_from_s3(report_id, report_type)
            if not report:
                logger.error(f"Report {report_id} not found")
                await db_service.update_report_status(report_id, ReportStatus.FAILED)
                return None
            
            # Generate the summary
            summary = await self.ai_generator.generate_summary(
                report_id=report_id,
                report_type=report_type,
                report_text=report.content
            )
            
            # Create a unique ID for the summary
            summary_with_id = Summary(
                id=str(uuid.uuid4()),
                report_id=summary.report_id,
                report_type=summary.report_type,
                summary_text=summary.summary_text,
                key_findings=summary.key_findings,
                recommendations=summary.recommendations,
                metadata=summary.metadata
            )
            
            # Save the summary to the database
            await db_service.save_summary(summary_with_id)
            
            # Publish the summary to Kafka
            await self.publish_summary(summary_with_id)
            
            logger.info(f"Summary generated for report {report_id}")
            return summary_with_id
            
        except Exception as e:
            logger.error(f"Error summarizing report {report_id}: {e}")
            await db_service.update_report_status(report_id, ReportStatus.FAILED)
            return None
    
    async def publish_summary(self, summary: Summary):
        """Publish a summary to Kafka"""
        try:
            if self.producer is None:
                await self.init_kafka_producer()
                
            # Convert summary to JSON
            summary_json = summary.model_dump_json()
            
            # Publish to Kafka
            await self.producer.send_and_wait(
                topic=settings.KAFKA_TOPIC_SUMMARIES,
                value=summary_json.encode()
            )
            
            logger.info(f"Published summary for report {summary.report_id} to Kafka")
            
        except Exception as e:
            logger.error(f"Error publishing summary to Kafka: {e}")
    
    async def batch_process_pending_reports(self, batch_size: int = 10):
        """Process a batch of pending reports"""
        try:
            # Get pending reports
            pending_reports = await db_service.get_pending_reports(limit=batch_size)
            logger.info(f"Found {len(pending_reports)} pending reports to process")
            
            # Process each report
            for report in pending_reports:
                try:
                    await self.summarize_report(
                        report_id=report["id"],
                        report_type=report["type"]
                    )
                except Exception as e:
                    logger.error(f"Error processing report {report['id']}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error batch processing reports: {e}")


# Create a global instance for use in other modules
summarization_service = SummarizationService()