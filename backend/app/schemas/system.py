"""System and module schemas"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# System schemas
class SystemBase(BaseModel):
    name: str
    description: Optional[str] = None


class SystemCreate(SystemBase):
    pass


class SystemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SystemResponse(SystemBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Module schemas
class ModuleBase(BaseModel):
    name: str
    description: Optional[str] = None


class ModuleCreate(ModuleBase):
    parent_id: Optional[int] = None


class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


class ModuleResponse(ModuleBase):
    id: int
    system_id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModuleTreeResponse(ModuleResponse):
    children: List["ModuleTreeResponse"] = []

    class Config:
        from_attributes = True


# Case Field schemas
class CaseFieldBase(BaseModel):
    field_name: str
    field_label: str
    field_type: str = "text"
    is_required: bool = False
    is_visible: bool = True
    sort_order: int = 0


class CaseFieldCreate(CaseFieldBase):
    pass


class CaseFieldUpdate(BaseModel):
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    is_required: Optional[bool] = None
    is_visible: Optional[bool] = None
    sort_order: Optional[int] = None


class CaseFieldResponse(CaseFieldBase):
    id: int
    system_id: int

    class Config:
        from_attributes = True


# Import Optional for later use
from typing import Optional
