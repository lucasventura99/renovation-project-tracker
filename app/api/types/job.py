# app/api/types/job.py
import strawberry
from decimal import Decimal
from typing import Optional
from datetime import datetime

@strawberry.type
class JobType:
    id: int
    description: str
    location: str
    cost: Decimal
    status: str
    created_at: datetime
    updated_at: datetime