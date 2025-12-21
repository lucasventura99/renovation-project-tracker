# app/models/history.py
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import String, ForeignKey, DateTime, func, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class JobHistory(Base):
    __tablename__ = "job_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # The Memento (Snapshot)
    snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")