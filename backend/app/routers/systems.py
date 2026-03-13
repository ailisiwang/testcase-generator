"""Test system routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.system import (
    SystemCreate, SystemUpdate, SystemResponse,
    CaseFieldCreate, CaseFieldUpdate, CaseFieldResponse
)
from app.models.system import TestSystem
from app.models.user import User
from app.routers.users import get_current_user_dep

router = APIRouter(prefix="/api/systems", tags=["测试系统"])
security = HTTPBearer()


@router.get("", response_model=List[SystemResponse])
def get_systems(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get test systems list"""
    systems = db.query(TestSystem).filter(
        TestSystem.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return systems


@router.post("", response_model=SystemResponse, status_code=status.HTTP_201_CREATED)
def create_system(
    system_data: SystemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Create a new test system"""
    system = TestSystem(
        name=system_data.name,
        description=system_data.description,
        user_id=current_user.id,
        creator_id=current_user.id
    )
    
    db.add(system)
    db.commit()
    db.refresh(system)
    
    return system


@router.get("/{system_id}", response_model=SystemResponse)
def get_system(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get system by ID"""
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    return system


@router.put("/{system_id}", response_model=SystemResponse)
def update_system(
    system_id: int,
    system_data: SystemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Update system"""
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    if system_data.name is not None:
        system.name = system_data.name
    if system_data.description is not None:
        system.description = system_data.description
    
    db.commit()
    db.refresh(system)
    
    return system


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Delete system"""
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    db.delete(system)
    db.commit()
    
    return None


# Field configuration routes
@router.get("/{system_id}/fields", response_model=List[CaseFieldResponse])
def get_fields(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get case fields for a system"""
    # Verify ownership
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    from app.models.test_case import CaseField
    fields = db.query(CaseField).filter(
        CaseField.system_id == system_id
    ).order_by(CaseField.sort_order).all()
    
    return fields


@router.put("/{system_id}/fields", response_model=List[CaseFieldResponse])
def update_fields(
    system_id: int,
    fields_data: List[CaseFieldCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Update case fields for a system"""
    # Verify ownership
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    from app.models.test_case import CaseField
    
    # Delete existing fields
    db.query(CaseField).filter(CaseField.system_id == system_id).delete()
    
    # Create new fields
    new_fields = []
    for idx, field_data in enumerate(fields_data):
        field = CaseField(
            system_id=system_id,
            field_name=field_data.field_name,
            field_label=field_data.field_label,
            field_type=field_data.field_type,
            is_required=1 if field_data.is_required else 0,
            is_visible=1 if field_data.is_visible else 0,
            sort_order=field_data.sort_order or idx
        )
        db.add(field)
        new_fields.append(field)
    
    db.commit()
    
    for field in new_fields:
        db.refresh(field)
    
    return new_fields
