# app/models/job.py
import enum
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Enum, Numeric, ForeignKey, DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
# We import User only for type checking to avoid runtime circular imports
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class JobStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class Job(Base):
    __tablename__ = "jobs"

    description: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    
    # Precision 10, scale 2 = up to 99,999,999.99
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PLANNING, nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Foreign Keys
    contractor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    homeowner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    contractor: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[contractor_id], 
        back_populates="contractor_jobs"
    )
    homeowner: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[homeowner_id], 
        back_populates="homeowner_jobs"
    )
    current_version: Mapped[int] = mapped_column(Integer, default=0)
    def to_dict(self) -> dict:
        """Serializes the job state for history tracking."""
        return {
            "description": self.description,
            "location": self.location,
            "cost": float(self.cost), # JSON doesn't support Decimal natively
            "status": self.status.value,
            "contractor_id": self.contractor_id,
            "homeowner_id": self.homeowner_id,
        }