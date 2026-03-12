"""Test system model"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class TestSystem(Base):
    __tablename__ = "test_systems"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", backref="systems")
    modules = relationship("Module", back_populates="system", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="system", cascade="all, delete-orphan")
    fields = relationship("CaseField", back_populates="system", cascade="all, delete-orphan")
