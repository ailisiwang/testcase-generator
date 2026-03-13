"""Test case routes"""
from typing import List, Optional
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.schemas.case import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    CaseGenerateRequest, CaseGenerateFileRequest,
    PaginatedTestCases
)
from app.models.test_case import TestCase, CaseVersion, CaseField
from app.models.system import TestSystem
from app.models.user import User
from app.routers.users import get_current_user_dep
from app.services.case_generator import CaseGeneratorService
from app.utils.excel import export_cases_to_excel

router = APIRouter(prefix="/api/cases", tags=["用例管理"])
security = HTTPBearer()


@router.get("", response_model=PaginatedTestCases)

# Export route
@router.get("/export")
async def export_cases(
    system_id: Optional[int] = None,
    module_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Export cases to Excel"""
    query = db.query(TestCase).join(TestSystem).filter(
        TestSystem.user_id == current_user.id
    )
    
    if system_id:
        query = query.filter(TestCase.system_id == system_id)
    if module_id:
        query = query.filter(TestCase.module_id == module_id)
    if status:
        query = query.filter(TestCase.status == status)
    
    cases = query.all()
    
    # Get fields
    if system_id:
        fields = db.query(CaseField).filter(
            CaseField.system_id == system_id
        ).order_by(CaseField.sort_order).all()
    else:
        fields = []
    
    # Export to Excel
    excel_data = export_cases_to_excel(cases, fields)
    
    return StreamingResponse(
        iter([excel_data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=test_cases.xlsx"}
    )

def get_cases(
    system_id: Optional[int] = None,
    module_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get test cases with pagination"""
    query = db.query(TestCase).join(TestSystem).filter(
        TestSystem.user_id == current_user.id
    )
    
    if system_id:
        query = query.filter(TestCase.system_id == system_id)
    if module_id:
        query = query.filter(TestCase.module_id == module_id)
    if status:
        query = query.filter(TestCase.status == status)
    
    total = query.count()
    pages = math.ceil(total / page_size)
    
    cases = query.order_by(desc(TestCase.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return {
        "items": cases,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Create a new test case"""
    # Verify system ownership
    system = db.query(TestSystem).filter(
        TestSystem.id == case_data.system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    # Verify module if provided
    if case_data.module_id:
        module = db.query(TestCase).filter(
            TestCase.id == case_data.module_id
        ).first()
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    case = TestCase(
        system_id=case_data.system_id,
        module_id=case_data.module_id,
        case_data=case_data.case_data,
        created_by=current_user.id,
        version=1
    )
    
    db.add(case)
    db.commit()
    db.refresh(case)
    
    # Create initial version
    version = CaseVersion(
        case_id=case.id,
        version=1,
        case_data=case.case_data,
        change_summary="初始版本",
        created_by=current_user.id
    )
    db.add(version)
    db.commit()
    
    return case


@router.get("/{case_id}", response_model=TestCaseResponse)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get test case by ID"""
    case = db.query(TestCase).join(TestSystem).filter(
        TestCase.id == case_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")
    
    return case


@router.put("/{case_id}", response_model=TestCaseResponse)
def update_case(
    case_id: int,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Update test case"""
    case = db.query(TestCase).join(TestSystem).filter(
        TestCase.id == case_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")
    
    # Check if creating new version
    if case_data.case_data and case_data.case_data != case.case_data:
        # Create new version
        case.version += 1
        version = CaseVersion(
            case_id=case.id,
            version=case.version,
            case_data=case_data.case_data,
            change_summary="更新用例",
            created_by=current_user.id
        )
        db.add(version)
        case.case_data = case_data.case_data
    
    if case_data.module_id is not None:
        case.module_id = case_data.module_id
    if case_data.status is not None:
        case.status = case_data.status
    if case_data.review_status is not None:
        case.review_status = case_data.review_status
    
    db.commit()
    db.refresh(case)
    
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Delete test case"""
    case = db.query(TestCase).join(TestSystem).filter(
        TestCase.id == case_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")
    
    db.delete(case)
    db.commit()
    
    return None


@router.get("/{case_id}/versions", response_model=List)
def get_case_versions(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get case version history"""
    case = db.query(TestCase).join(TestSystem).filter(
        TestCase.id == case_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")
    
    versions = db.query(CaseVersion).filter(
        CaseVersion.case_id == case_id
    ).order_by(desc(CaseVersion.version)).all()
    
    return versions


# Generation routes
@router.post("/generate")
async def generate_cases(
    request: CaseGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Generate test cases using LLM"""
    # Verify system ownership
    system = db.query(TestSystem).filter(
        TestSystem.id == request.system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    try:
        cases = await CaseGeneratorService.generate_cases(
            db=db,
            system_id=request.system_id,
            requirement=request.requirement,
            model_config_id=request.model_config_id,
            count=request.count,
            user_id=current_user.id
        )
        
        return {
            "cases": cases,
            "count": len(cases)
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def export_cases(
    system_id: Optional[int] = None,
    module_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Export cases to Excel"""
    query = db.query(TestCase).join(TestSystem).filter(
        TestSystem.user_id == current_user.id
    )
    
    if system_id:
        query = query.filter(TestCase.system_id == system_id)
    if module_id:
        query = query.filter(TestCase.module_id == module_id)
    if status:
        query = query.filter(TestCase.status == status)
    
    cases = query.all()
    
    # Get fields
    if system_id:
        fields = db.query(CaseField).filter(
            CaseField.system_id == system_id
        ).order_by(CaseField.sort_order).all()
    else:
        fields = []
    
    # Export to Excel
    excel_data = export_cases_to_excel(
        cases=[{"case_data": c.case_data} for c in cases],
        fields=[{
            "field_name": f.field_name,
            "field_label": f.field_label,
            "is_visible": f.is_visible
        } for f in fields]
    )
    
    return StreamingResponse(
        iter([excel_data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=test_cases.xlsx"
        }
    )



