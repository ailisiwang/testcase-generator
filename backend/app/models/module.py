"""Module model"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("test_systems.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    system = relationship("TestSystem", back_populates="modules")
    parent = relationship("Module", remote_side=[id], backref="children")
    test_cases = relationship("TestCase", back_populates="module")
