"""Model config routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.model_config import (
    ModelConfigCreate, ModelConfigUpdate, 
    ModelConfigResponse, AVAILABLE_PROVIDERS
)
from app.models.model_config import ModelConfig
from app.models.user import User
from app.routers.users import get_current_user_dep
from app.utils.security import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/api/models", tags=["模型配置"])
security = HTTPBearer()


@router.get("/providers")
def get_providers():
    """Get available LLM providers"""
    return AVAILABLE_PROVIDERS


@router.get("", response_model=List[ModelConfigResponse])
def get_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get model configurations"""
    configs = db.query(ModelConfig).filter(
        ModelConfig.user_id == current_user.id
    ).order_by(ModelConfig.created_at.desc()).all()
    
    # Mask API keys
    for config in configs:
        if config.api_key_encrypted:
            config.api_key_encrypted = "***"
    
    return configs


@router.post("", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_model_config(
    config_data: ModelConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Create a new model configuration"""
    # Validate provider - allow custom and predefined
    provider_ids = [p.id for p in AVAILABLE_PROVIDERS]
    provider_ids.append("custom")  # Allow custom provider
    if config_data.provider not in provider_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的供应商: {config_data.provider}"
        )
    
    # Encrypt API key
    api_key_encrypted = None
    if config_data.api_key:
        api_key_encrypted = encrypt_api_key(config_data.api_key)
    
    config = ModelConfig(
        user_id=current_user.id,
        created_by=current_user.id,
        name=config_data.name,
        provider=config_data.provider,
        model_name=config_data.model_name,
        api_key_encrypted=api_key_encrypted,
        api_base_url=config_data.api_base_url,
        temperature=config_data.temperature,
        max_tokens=config_data.max_tokens
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    # Mask API key in response
    config.api_key_encrypted = "***"
    
    return config


@router.get("/{config_id}", response_model=ModelConfigResponse)
def get_model_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Get model configuration by ID"""
    config = db.query(ModelConfig).filter(
        ModelConfig.id == config_id,
        ModelConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    
    # Mask API key
    if config.api_key_encrypted:
        config.api_key_encrypted = "***"
    
    return config


@router.put("/{config_id}", response_model=ModelConfigResponse)
def update_model_config(
    config_id: int,
    config_data: ModelConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Update model configuration"""
    config = db.query(ModelConfig).filter(
        ModelConfig.id == config_id,
        ModelConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    
    if config_data.model_name is not None:
        config.model_name = config_data.model_name
    
    if config_data.api_key is not None:
        config.api_key_encrypted = encrypt_api_key(config_data.api_key)
    
    if config_data.api_base_url is not None:
        config.api_base_url = config_data.api_base_url
    
    if config_data.temperature is not None:
        config.temperature = config_data.temperature
    
    if config_data.max_tokens is not None:
        config.max_tokens = config_data.max_tokens
    
    if config_data.is_active is not None:
        config.is_active = config_data.is_active
    
    db.commit()
    db.refresh(config)
    
    # Mask API key
    if config.api_key_encrypted:
        config.api_key_encrypted = "***"
    
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dep)
):
    """Delete model configuration"""
    config = db.query(ModelConfig).filter(
        ModelConfig.id == config_id,
        ModelConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置不存在")
    
    db.delete(config)
    db.commit()
    
    return None
