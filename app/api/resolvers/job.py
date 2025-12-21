# app/api/resolvers/job.py
import strawberry
from typing import List, Optional
from decimal import Decimal
from strawberry.types import Info

from app.api.types.job import JobType
from app.services.job_service import JobService
from app.models.job import Job, JobStatus

def map_job_model_to_type(job: Job) -> JobType:
    return JobType(
        id=job.id,
        description=job.description,
        location=job.location,
        cost=job.cost,
        status=job.status.value,
        created_at=job.created_at,
        updated_at=job.updated_at,
        current_version=job.current_version,
    )
@strawberry.type
class JobQuery:
    @strawberry.field
    async def my_jobs(self, info: Info) -> List[JobType]:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
            
        jobs = await JobService.get_jobs_for_user(info.context["db"], user)
        # Use the helper function
        return [map_job_model_to_type(job) for job in jobs]
    @strawberry.field
    async def job(self, info: Info, job_id: int) -> Optional[JobType]:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
            
        job = await JobService.get_job_by_id(info.context["db"], user, job_id)
        if not job:
            return None
            
        return map_job_model_to_type(job)
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
        return map_job_model_to_type(job)

    @strawberry.mutation
    async def update_job_status(
        self, info: Info, job_id: int, status: str
    ) -> JobType:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
            
        try:
            new_status = JobStatus(status)
        except ValueError:
            raise Exception(f"Invalid status. Must be one of: {[s.value for s in JobStatus]}")

        job = await JobService.update_job_status(
            info.context["db"], user, job_id, new_status
        )
        return map_job_model_to_type(job)

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
        return map_job_model_to_type(job)

    @strawberry.mutation
    async def undo_last_change(self, info: Info, job_id: int) -> JobType:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
        
        db = info.context["db"]
        
        try:
            job = await JobService.undo_last_change(db, user, job_id)
            return map_job_model_to_type(job)
        except ValueError as e:
            raise Exception(str(e))
        except PermissionError as e:
            raise Exception(str(e))

    @strawberry.mutation
    async def redo_last_change(self, info: Info, job_id: int) -> JobType:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")
            
        db = info.context["db"]
        
        try:
            job = await JobService.redo_last_change(db, user, job_id)
            return map_job_model_to_type(job)
        except ValueError as e:
            raise Exception(str(e))
    
    @strawberry.mutation
    async def update_job_details(
        self, info: Info, job_id: int, description: str, location: str, cost: Decimal
    ) -> JobType:
        user = info.context.get("user")
        if not user:
            raise Exception("Not authenticated")

        job = await JobService.update_job_details(
            info.context["db"], user, job_id, description, location, cost
        )
        return map_job_model_to_type(job)