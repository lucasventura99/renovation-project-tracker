from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.job import Job

class SubTask(Base):
    __tablename__ = "subtasks"

    description: Mapped[str] = mapped_column(String, nullable=False)
    # Precision 10, scale 2
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    
    job: Mapped["Job"] = relationship("Job", back_populates="subtasks")