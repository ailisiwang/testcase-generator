"""Test case models"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("test_systems.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    case_data = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    status = Column(String(20), default="draft")  # draft, active, archived
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    system = relationship("TestSystem", back_populates="test_cases")
    module = relationship("Module", back_populates="test_cases")
    creator = relationship("User", foreign_keys=[created_by], backref="created_cases")
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="reviewed_cases")
    versions = relationship("CaseVersion", back_populates="case", cascade="all, delete-orphan")


class CaseVersion(Base):
    __tablename__ = "case_versions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    case_data = Column(JSON, nullable=False)
    change_summary = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    case = relationship("TestCase", back_populates="versions")
    creator = relationship("User")


class CaseField(Base):
    __tablename__ = "case_fields"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("test_systems.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(50), nullable=False)
    field_label = Column(String(100), nullable=False)
    field_type = Column(String(20), default="text")  # text, textarea, select, radio, checkbox
    is_required = Column(Integer, default=0)
    is_visible = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    system = relationship("TestSystem", back_populates="fields")
