# app/models/user.py
import enum
from typing import List
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class UserRole(str, enum.Enum):
    CONTRACTOR = "CONTRACTOR"
    HOMEOWNER = "HOMEOWNER"

class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.HOMEOWNER, nullable=False)

    # Relationships
    # We use string references "Job" to avoid circular imports 
    # (because Job will also import User)
    contractor_jobs: Mapped[List["Job"]] = relationship(
        "Job", 
        back_populates="contractor", 
        foreign_keys="[Job.contractor_id]"
    )
    
    homeowner_jobs: Mapped[List["Job"]] = relationship(
        "Job", 
        back_populates="homeowner", 
        foreign_keys="[Job.homeowner_id]"
    )