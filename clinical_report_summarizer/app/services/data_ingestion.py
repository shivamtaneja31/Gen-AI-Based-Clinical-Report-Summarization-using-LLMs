import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiokafka
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.domain.models import ClinicalReport, ReportType, ReportStatus

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting clinical reports from various sources"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        
    async def process_kafka_messages(self):
        """Process incoming messages from Kafka"""
        logger.info("Starting Kafka consumer for clinical reports")
        
        consumer = aiokafka.AIOKafkaConsumer(
            settings.KAFKA_TOPIC_REPORTS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            auto_offset_reset="earliest",
        )
        
        try:
            await consumer.start()
            logger.info(f"Connected to Kafka topic: {settings.KAFKA_TOPIC_REPORTS}")
            
            async for message in consumer:
                try:
                    report_data = json.loads(message.value.decode())
                    logger.info(f"Received message: {report_data}")
                    
                    # Create a clinical report object
                    report = ClinicalReport(
                        id=report_data.get("id", str(uuid.uuid4())),
                        type=report_data.get("type"),
                        content=report_data.get("content", ""),
                        patient_id=report_data.get("patient_id"),
                        provider_id=report_data.get("provider_id"),
                        status=ReportStatus.PENDING,
                        metadata=report_data.get("metadata", {})
                    )
                    
                    # Store the report in S3
                    await self.store_report_in_s3(report)
                    
                    # Submit for summarization (this would typically trigger a task)
                    # Implementation in summarization_tasks.py
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        finally:
            await consumer.stop()
    
    async def ingest_report_from_file(self, file_path: str, report_type: ReportType,
                               patient_id: str, provider_id: str,
                               metadata: Optional[Dict[str, Any]] = None) -> ClinicalReport:
        """Ingest a clinical report from a file"""
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            
            report = ClinicalReport(
                id=str(uuid.uuid4()),
                type=report_type,
                content=content,
                patient_id=patient_id,
                provider_id=provider_id,
                status=ReportStatus.PENDING,
                metadata=metadata or {}
            )
            
            await self.store_report_in_s3(report)
            return report
            
        except Exception as e:
            logger.error(f"Error ingesting report from file {file_path}: {e}")
            raise
    
    async def ingest_report(self, content: str, report_type: ReportType,
                     patient_id: str, provider_id: str,
                     metadata: Optional[Dict[str, Any]] = None) -> ClinicalReport:
        """Ingest a clinical report from content string"""
        try:
            report = ClinicalReport(
                id=str(uuid.uuid4()),
                type=report_type,
                content=content,
                patient_id=patient_id,
                provider_id=provider_id,
                status=ReportStatus.PENDING,
                metadata=metadata or {}
            )
            
            await self.store_report_in_s3(report)
            return report
            
        except Exception as e:
            logger.error(f"Error ingesting report: {e}")
            raise
    
    async def store_report_in_s3(self, report: ClinicalReport) -> bool:
        """Store a clinical report in S3"""
        try:
            # Create a JSON representation of the report
            report_json = report.model_dump_json()
            
            # Create the S3 object key based on report type and date
            date_str = datetime.now().strftime("%Y/%m/%d")
            object_key = f"reports/{report.type}/{date_str}/{report.id}.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=report_json,
                ContentType='application/json'
            )
            
            logger.info(f"Stored report {report.id} in S3: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error storing report in S3: {e}")
            return False
    
    async def get_report_from_s3(self, report_id: str, report_type: ReportType) -> Optional[ClinicalReport]:
        """Get a clinical report from S3"""
        try:
            # Query for the report object
            # Note: In a real implementation, you might need to query a database first to get the S3 path
            paginator = self.s3_client.get_paginator('list_objects_v2')
            prefix = f"reports/{report_type}/"
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if "Contents" not in page:
                    continue
                    
                for obj in page["Contents"]:
                    if obj["Key"].endswith(f"/{report_id}.json"):
                        # Found the report
                        response = self.s3_client.get_object(
                            Bucket=self.bucket_name, 
                            Key=obj["Key"]
                        )
                        report_json = response["Body"].read().decode('utf-8')
                        return ClinicalReport.model_validate_json(report_json)
            
            logger.warning(f"Report {report_id} of type {report_type} not found in S3")
            return None
            
        except ClientError as e:
            logger.error(f"Error retrieving report from S3: {e}")
            return None


# Create a global instance for use in other modules
data_ingestion_service = DataIngestionService()