from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReportType(str, Enum):
    DISCHARGE_NOTE = "discharge_note"
    RADIOLOGY_REPORT = "radiology_report"
    LAB_RESULT = "lab_result"


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClinicalReport(BaseModel):
    id: str
    type: ReportType
    content: str
    patient_id: str
    provider_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: ReportStatus = ReportStatus.PENDING
    metadata: Dict[str, Any] = {}


class Summary(BaseModel):
    id: str
    report_id: str
    report_type: ReportType
    summary_text: str
    key_findings: List[str]
    recommendations: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}


class SummaryRequest(BaseModel):
    report_id: str
    report_type: ReportType
    priority: Optional[int] = 1  # 1 (highest) to 5 (lowest)


class ReportWithSummary(BaseModel):
    report: ClinicalReport
    summary: Optional[Summary] = None


class User(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    department: Optional[str] = None


class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RADIOLOGIST = "radiologist"
    LAB_TECHNICIAN = "lab_technician"