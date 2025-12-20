# app/services/job_service.py
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobStatus
from app.models.user import User, UserRole

class JobService:
    @staticmethod
    async def create_job(
        session: AsyncSession, 
        user: User, 
        description: str, 
        location: str, 
        cost: Decimal
    ) -> Job:
        # Rule: Only Contractors can create jobs
        if user.role != UserRole.CONTRACTOR:
            raise PermissionError("Only contractors can create jobs.")

        job = Job(
            description=description,
            location=location,
            cost=cost,
            contractor_id=user.id,
            status=JobStatus.PLANNING
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def get_jobs_for_user(session: AsyncSession, user: User) -> List[Job]:
        # Rule: Contractors see their created jobs
        if user.role == UserRole.CONTRACTOR:
            query = select(Job).where(Job.contractor_id == user.id)
        # Rule: Homeowners see jobs assigned to them
        else:
            query = select(Job).where(Job.homeowner_id == user.id)
            
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_job_status(
        session: AsyncSession, 
        user: User, 
        job_id: int, 
        status: JobStatus
    ) -> Job:
        # 1. Fetch Job
        query = select(Job).where(Job.id == job_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError("Job not found")

        # 2. Authorization Check (Must be the job's contractor)
        if job.contractor_id != user.id:
            raise PermissionError("You do not have permission to modify this job")

        # 3. Update
        job.status = status
        await session.commit()
        await session.refresh(job)
        return job
        
    @staticmethod
    async def assign_homeowner(
        session: AsyncSession,
        user: User,
        job_id: int,
        homeowner_email: str
    ) -> Job:
        # 1. Fetch Job
        query = select(Job).where(Job.id == job_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError("Job not found")
            
        if job.contractor_id != user.id:
            raise PermissionError("Not authorized")
            
        # 2. Find Homeowner
        user_query = select(User).where(User.email == homeowner_email)
        user_result = await session.execute(user_query)
        homeowner = user_result.scalar_one_or_none()
        
        if not homeowner or homeowner.role != UserRole.HOMEOWNER:
             raise ValueError("Homeowner user not found")
             
        # 3. Assign
        job.homeowner_id = homeowner.id
        await session.commit()
        await session.refresh(job)
        return job