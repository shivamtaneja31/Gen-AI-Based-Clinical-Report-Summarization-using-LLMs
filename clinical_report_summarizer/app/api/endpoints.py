from typing import Dict, List, Optional, Any
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.domain.models import (
    ReportType, ClinicalReport, Summary, SummaryRequest, ReportWithSummary, User
)
from app.api.security import (
    TokenPayload, get_current_user, 
    requires_admin, requires_doctor, requires_nurse, requires_radiologist, requires_lab_technician
)
from app.services.data_ingestion import data_ingestion_service
from app.services.storage import db_service
from app.tasks.summarization_tasks import summarize_report

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    type: str
    patient_id: str
    provider_id: str
    status: str
    created_at: str
    metadata: Dict[str, Any] = {}


class ReportUploadRequest(BaseModel):
    patient_id: str
    report_type: ReportType
    metadata: Optional[Dict[str, Any]] = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@router.post("/reports", response_model=ReportResponse)
async def create_report(
    patient_id: str = Form(...),
    report_type: ReportType = Form(...),
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: TokenPayload = Depends(requires_doctor),
):
    """Create a new clinical report"""
    try:
        # Create metadata
        metadata = {
            "created_by": current_user.preferred_username,
            "source": "direct_input" if not file else "file_upload",
        }
        
        # If content is empty but file is provided, read from file
        report_content = content
        if not content and file:
            report_content = await file.read()
            report_content = report_content.decode("utf-8")
        
        if not report_content:
            raise HTTPException(
                status_code=400,
                detail="Report content is required either as direct input or file upload"
            )
        
        # Create the report
        report = await data_ingestion_service.ingest_report(
            content=report_content,
            report_type=report_type,
            patient_id=patient_id,
            provider_id=current_user.sub,
            metadata=metadata
        )
        
        # Save report metadata
        await db_service.save_report_metadata(report)
        
        # Submit for summarization as a background task
        summarize_report.delay(
            report_id=report.id,
            report_type=report.type
        )
        
        return {
            "id": report.id,
            "type": report.type,
            "patient_id": report.patient_id,
            "provider_id": report.provider_id,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "metadata": report.metadata
        }
        
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create report: {str(e)}"
        )


@router.get("/reports/{report_id}", response_model=dict)
async def get_report(
    report_id: str,
    with_summary: bool = True,
    current_user: TokenPayload = Depends(requires_nurse),
):
    """Get a clinical report by ID"""
    try:
        # Get report metadata
        report_meta = await db_service.get_report_metadata(report_id)
        if not report_meta:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found"
            )
        
        # Get the full report from S3
        report = await data_ingestion_service.get_report_from_s3(
            report_id=report_id,
            report_type=report_meta["type"]
        )
        
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} content not found"
            )
        
        result = {
            "id": report.id,
            "type": report.type,
            "patient_id": report.patient_id,
            "provider_id": report.provider_id,
            "content": report.content,
            "status": report.status,
            "created_at": report.created_at.isoformat(),
            "metadata": report.metadata
        }
        
        # Include summary if requested
        if with_summary:
            summary = await db_service.get_summary(report_id)
            if summary:
                result["summary"] = summary
        
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )


@router.get("/reports", response_model=List[dict])
async def search_reports(
    patient_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    report_type: Optional[ReportType] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenPayload = Depends(requires_nurse),
):
    """Search for clinical reports"""
    try:
        reports = await db_service.search_reports(
            patient_id=patient_id,
            provider_id=provider_id,
            report_type=report_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        
        return reports
        
    except Exception as e:
        logger.error(f"Error searching reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search reports: {str(e)}"
        )


@router.post("/reports/{report_id}/summarize", response_model=dict)
async def request_summarization(
    report_id: str,
    current_user: TokenPayload = Depends(requires_doctor),
):
    """Request summarization for a report"""
    try:
        # Check if report exists
        report_meta = await db_service.get_report_metadata(report_id)
        if not report_meta:
            raise HTTPException(
                status_code=404,
                detail=f"Report {report_id} not found"
            )
        
        # Submit the summarization task
        task = summarize_report.delay(
            report_id=report_id,
            report_type=report_meta["type"]
        )
        
        return {
            "message": f"Summarization requested for report {report_id}",
            "task_id": task.id,
            "report_id": report_id
        }
        
    except Exception as e:
        logger.error(f"Error requesting summarization for report {report_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to request summarization: {str(e)}"
        )


@router.get("/patients/{patient_id}/reports", response_model=List[dict])
async def get_patient_reports(
    patient_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: TokenPayload = Depends(requires_nurse),
):
    """Get all reports for a specific patient"""
    try:
        reports = await db_service.get_reports_by_patient(
            patient_id=patient_id,
            limit=limit,
            offset=offset
        )
        
        return reports
        
    except Exception as e:
        logger.error(f"Error retrieving reports for patient {patient_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve patient reports: {str(e)}"
        )


@router.get("/reports/{report_id}/summary", response_model=dict)
async def get_report_summary(
    report_id: str,
    current_user: TokenPayload = Depends(requires_nurse),
):
    """Get the summary for a specific report"""
    try:
        summary = await db_service.get_summary(report_id)
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"Summary for report {report_id} not found"
            )
        
        return summary
        
    except Exception as e:
        logger.error(f"Error retrieving summary for report {report_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve summary: {str(e)}"
        )