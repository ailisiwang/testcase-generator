"""Module routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.system import ModuleCreate, ModuleUpdate, ModuleResponse, ModuleTreeResponse
from app.models.module import Module
from app.models.user import User
from app.routers.users import get_current_user_dep

router = APIRouter(prefix="/api/modules", tags=["模块管理"])
security = HTTPBearer()


@router.get("/system/{system_id}", response_model=List[ModuleResponse])
def get_modules(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get modules for a system"""
    # Verify system belongs to user
    from app.models.system import TestSystem
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    modules = db.query(Module).filter(Module.system_id == system_id).all()
    return modules


@router.get("/system/{system_id}/tree", response_model=List[ModuleTreeResponse])
def get_module_tree(
    system_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get module tree for a system"""
    from app.models.system import TestSystem
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    # Get root modules (no parent)
    modules = db.query(Module).filter(
        Module.system_id == system_id,
        Module.parent_id == None
    ).all()
    
    def build_tree(module: Module) -> ModuleTreeResponse:
        children = [
            build_tree(child) 
            for child in db.query(Module).filter(Module.parent_id == module.id).all()
        ]
        return ModuleTreeResponse(
            id=module.id,
            system_id=module.system_id,
            name=module.name,
            parent_id=module.parent_id,
            description=module.description,
            created_at=module.created_at,
            updated_at=module.updated_at,
            children=children
        )
    
    return [build_tree(m) for m in modules]


@router.post("/system/{system_id}", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
def create_module(
    system_id: int,
    module_data: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Create a new module"""
    from app.models.system import TestSystem
    system = db.query(TestSystem).filter(
        TestSystem.id == system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="系统不存在")
    
    # Verify parent if provided
    if module_data.parent_id:
        parent = db.query(Module).filter(
            Module.id == module_data.parent_id,
            Module.system_id == system_id
        ).first()
        
        if not parent:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父模块不存在")
    
    module = Module(
        system_id=system_id,
        name=module_data.name,
        description=module_data.description,
        parent_id=module_data.parent_id
    )
    
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return module


@router.get("/{module_id}", response_model=ModuleResponse)
def get_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get module by ID"""
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    # Verify ownership through system
    from app.models.system import TestSystem
    system = db.query(TestSystem).filter(
        TestSystem.id == module.system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    
    return module


@router.put("/{module_id}", response_model=ModuleResponse)
def update_module(
    module_id: int,
    module_data: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Update module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    # Verify ownership
    from app.models.system import TestSystem
    system = db.query(TestSystem).filter(
        TestSystem.id == module.system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    
    if module_data.name is not None:
        module.name = module_data.name
    if module_data.description is not None:
        module.description = module_data.description
    if module_data.parent_id is not None:
        # Verify new parent
        if module_data.parent_id:
            parent = db.query(Module).filter(
                Module.id == module_data.parent_id,
                Module.system_id == module.system_id
            ).first()
            if not parent:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父模块不存在")
        module.parent_id = module_data.parent_id
    
    db.commit()
    db.refresh(module)
    
    return module


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Delete module"""
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模块不存在")
    
    # Verify ownership
    from app.models.system import TestSystem
    system = db.query(TestSystem).filter(
        TestSystem.id == module.system_id,
        TestSystem.user_id == current_user.id
    ).first()
    
    if not system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
    
    # Check for child modules
    children = db.query(Module).filter(Module.parent_id == module_id).count()
    if children > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="请先删除子模块"
        )
    
    db.delete(module)
    db.commit()
    
    return None
