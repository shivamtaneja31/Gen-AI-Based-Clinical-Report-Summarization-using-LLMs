import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Connection, Pool

from app.core.config import settings
from app.domain.models import Summary, ClinicalReport, ReportStatus, ReportType

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        
    async def init_pool(self):
        """Initialize the connection pool"""
        if self.pool is None:
            logger.info("Initializing database connection pool")
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=20
            )
            logger.info("Database connection pool initialized")
    
    async def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            logger.info("Closing database connection pool")
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def connection(self) -> Connection:
        """Get a connection from the pool"""
        if self.pool is None:
            await self.init_pool()
            
        async with self.pool.acquire() as conn:
            yield conn
    
    async def init_db(self):
        """Initialize the database schema"""
        async with self.connection() as conn:
            # Create reports table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clinical_reports (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    patient_id TEXT NOT NULL,
                    provider_id TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    metadata JSONB
                )
            ''')
            
            # Create summaries table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL REFERENCES clinical_reports(id),
                    report_type TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    key_findings JSONB NOT NULL,
                    recommendations JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB,
                    UNIQUE(report_id)
                )
            ''')
            
            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_patient_id ON clinical_reports(patient_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_provider_id ON clinical_reports(provider_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_type ON clinical_reports(type)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON clinical_reports(status)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_summaries_report_id ON summaries(report_id)')
            
            logger.info("Database schema initialized")
    
    async def save_report_metadata(self, report: ClinicalReport) -> bool:
        """Save report metadata to database (content stored in S3)"""
        try:
            async with self.connection() as conn:
                await conn.execute('''
                    INSERT INTO clinical_reports (id, type, patient_id, provider_id, status, created_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO UPDATE SET
                        status = $5,
                        metadata = $7
                ''', 
                report.id, 
                report.type, 
                report.patient_id, 
                report.provider_id,
                report.status,
                report.created_at,
                report.metadata
                )
                
                logger.info(f"Saved report metadata for {report.id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving report metadata: {e}")
            return False
    
    async def update_report_status(self, report_id: str, status: ReportStatus) -> bool:
        """Update the status of a report"""
        try:
            async with self.connection() as conn:
                await conn.execute('''
                    UPDATE clinical_reports
                    SET status = $1
                    WHERE id = $2
                ''', status, report_id)
                
                logger.info(f"Updated report {report_id} status to {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating report status: {e}")
            return False
    
    async def save_summary(self, summary: Summary) -> bool:
        """Save a summary to the database"""
        try:
            async with self.connection() as conn:
                await conn.execute('''
                    INSERT INTO summaries 
                    (id, report_id, report_type, summary_text, key_findings, recommendations, created_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (report_id) DO UPDATE SET
                        summary_text = $4,
                        key_findings = $5,
                        recommendations = $6,
                        metadata = $8
                ''',
                summary.id,
                summary.report_id,
                summary.report_type,
                summary.summary_text,
                summary.key_findings,
                summary.recommendations,
                summary.created_at,
                summary.metadata
                )
                
                # Update the report status to completed
                await self.update_report_status(summary.report_id, ReportStatus.COMPLETED)
                
                logger.info(f"Saved summary for report {summary.report_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            return False
    
    async def get_report_metadata(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report metadata from the database"""
        try:
            async with self.connection() as conn:
                row = await conn.fetchrow('''
                    SELECT id, type, patient_id, provider_id, status, created_at, metadata
                    FROM clinical_reports
                    WHERE id = $1
                ''', report_id)
                
                if not row:
                    return None
                    
                return dict(row)
                
        except Exception as e:
            logger.error(f"Error retrieving report metadata: {e}")
            return None
    
    async def get_summary(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary from the database"""
        try:
            async with self.connection() as conn:
                row = await conn.fetchrow('''
                    SELECT id, report_id, report_type, summary_text, key_findings, 
                           recommendations, created_at, metadata
                    FROM summaries
                    WHERE report_id = $1
                ''', report_id)
                
                if not row:
                    return None