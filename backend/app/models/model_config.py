"""Model config and operation log models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 配置名称
    provider = Column(String(20), nullable=False)  # glm, doubao, qwen, gpt, claude
    model_name = Column(String(50), nullable=False)
    api_key_encrypted = Column(Text, nullable=False)  # 数据库中此字段为 NOT NULL
    endpoint_url = Column(String(255), nullable=True)  # 旧字段，保留兼容
    api_base_url = Column(String(255), nullable=True)  # API 基础 URL
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    is_default = Column(Boolean, nullable=True)  # 是否为默认配置
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)  # 创建者 ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    owner = relationship("User", backref="model_configs")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="logs")
