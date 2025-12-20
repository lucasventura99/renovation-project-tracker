# app/api/resolvers/job.py
import strawberry
from typing import List, Optional
from decimal import Decimal
from strawberry.types import Info

from app.api.types.job import JobType
from app.services.job_service import JobService
from app.models.job import JobStatus

@strawberry.type
class JobQuery:
    @strawberry.field
    async def my_jobs(self, info: Info) -> List[JobType]:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
            
        jobs = await JobService.get_jobs_for_user(info.context["db"], user)
        # Convert SQLAlchemy models to Strawberry Types
        return [
            JobType(
                id=job.id,
                description=job.description,
                location=job.location,
                cost=job.cost,
                status=job.status.value,
                created_at=job.created_at,
                updated_at=job.updated_at
            ) for job in jobs
        ]

@strawberry.type
class JobMutation:
    @strawberry.mutation
    async def create_job(
        self, info: Info, description: str, location: str, cost: Decimal
    ) -> JobType:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")

        job = await JobService.create_job(
            info.context["db"], user, description, location, cost
        )
        
        return JobType(
            id=job.id,
            description=job.description,
            location=job.location,
            cost=job.cost,
            status=job.status.value,
            created_at=job.created_at,
            updated_at=job.updated_at
        )

    @strawberry.mutation
    async def assign_homeowner(
        self, info: Info, job_id: int, homeowner_email: str
    ) -> JobType:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
            
        job = await JobService.assign_homeowner(
            info.context["db"], user, job_id, homeowner_email
        )
        return JobType(
             id=job.id,
            description=job.description,
            location=job.location,
            cost=job.cost,
            status=job.status.value,
            created_at=job.created_at,
            updated_at=job.updated_at
        )