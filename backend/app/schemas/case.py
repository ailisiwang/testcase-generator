"""Test case schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# Test case schemas
class TestCaseBase(BaseModel):
    case_data: Dict[str, Any]


class TestCaseCreate(TestCaseBase):
    module_id: Optional[int] = None
    system_id: int


class TestCaseUpdate(BaseModel):
    case_data: Optional[Dict[str, Any]] = None
    module_id: Optional[int] = None
    status: Optional[str] = None
    review_status: Optional[str] = None


class TestCaseResponse(TestCaseBase):
    id: int
    system_id: int
    module_id: Optional[int] = None
    version: int
    status: str
    created_by: int
    reviewer_id: Optional[int] = None
    review_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Version schemas
class CaseVersionBase(BaseModel):
    version: int
    case_data: Dict[str, Any]
    change_summary: Optional[str] = None


class CaseVersionCreate(CaseVersionBase):
    case_id: int


class CaseVersionResponse(CaseVersionBase):
    id: int
    case_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# Generate schemas
class CaseGenerateRequest(BaseModel):
    system_id: int
    module_id: Optional[int] = None
    requirement: str
    model_config_id: Optional[int] = None
    count: int = 5


class CaseGenerateFileRequest(BaseModel):
    system_id: int
    model_config_id: Optional[int] = None
    count: int = 5


class GeneratedCase(BaseModel):
    case_data: Dict[str, Any]
    confidence: Optional[float] = None


class CaseGenerateResponse(BaseModel):
    task_id: str
    cases: List[GeneratedCase]


# Export schemas
class CaseExportRequest(BaseModel):
    system_id: Optional[int] = None
    module_id: Optional[int] = None
    status: Optional[str] = None
    format: str = "excel"


# Pagination
class PaginatedTestCases(BaseModel):
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int
    pages: int
