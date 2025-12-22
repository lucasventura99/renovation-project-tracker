from decimal import Decimal
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.models.history import JobHistory  # Ensure this is imported
from app.models.subtask import SubTask

class JobService:
    
    # --- HELPER: Snapshot Generation ---
    @staticmethod
    def _create_snapshot(job: Job) -> Dict[str, Any]:
        """Creates a JSON-serializable snapshot of the job state."""
        return {
            "description": job.description,
            "location": job.location,
            "cost": float(job.cost) if job.cost else 0.0,
            "status": job.status.value if hasattr(job.status, 'value') else job.status,
            "homeowner_id": job.homeowner_id
        }

    # --- HELPER: Centralized Update Logic ---
    @staticmethod
    async def _apply_versioned_update(
        session: AsyncSession, 
        user: User, 
        job: Job, 
        updates: Dict[str, Any], 
        action_type: str
    ) -> Job:
        """
        Applies updates, manages the timeline (burns future), and creates history.
        """
        # 1. Burn the Future: Delete any history ahead of current version
        # (e.g., if we undid to V2 and now save a change, V3 is invalid)
        await session.execute(
            delete(JobHistory).where(
                JobHistory.job_id == job.id,
                JobHistory.version > job.current_version
            )
        )

        # 2. Apply Updates to Job Object
        for field, value in updates.items():
            setattr(job, field, value)

        # 3. Increment Version
        job.current_version += 1

        # 4. Create History Record (The "After" State)
        history = JobHistory(
            job_id=job.id,
            changed_by_id=user.id,
            version=job.current_version,
            action_type=action_type,
            snapshot=JobService._create_snapshot(job)
        )
        session.add(history)
        
        # 5. Commit
        await session.commit()
        # Reload to ensure subtasks are loaded (refresh expires relationships)
        return await JobService.get_job_by_id(session, user, job.id)

    # --- CRUD METHODS ---

    @staticmethod
    async def create_job(
        session: AsyncSession, 
        user: User, 
        description: str, 
        location: str, 
        cost: Decimal
    ) -> Job:
        if user.role != UserRole.CONTRACTOR:
            raise PermissionError("Only contractors can create jobs.")

        # 1. Initialize Job at Version 1
        job = Job(
            description=description,
            location=location,
            cost=cost,
            contractor_id=user.id,
            status=JobStatus.PLANNING,
            current_version=1  # Start at 1
        )
        session.add(job)
        await session.flush() # Flush to get the ID

        # 2. Create Initial History (Version 1)
        history = JobHistory(
            job_id=job.id,
            changed_by_id=user.id,
            version=1,
            action_type="CREATED",
            snapshot=JobService._create_snapshot(job)
        )
        session.add(history)

        await session.commit()
        # Reload to ensure created_at and subtasks are populated
        return await JobService.get_job_by_id(session, user, job.id)

    @staticmethod
    async def update_job_details(
        session: AsyncSession, 
        user: User, 
        job_id: int, 
        description: str, 
        location: str,
        cost: Decimal
    ) -> Job:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job: raise ValueError("Job not found")
        if job.contractor_id != user.id: raise PermissionError("Unauthorized")

        # Delegate to versioned update helper
        return await JobService._apply_versioned_update(
            session, user, job,
            updates={
                "description": description, 
                "location": location, 
                "cost": cost
            },
            action_type="UPDATE_DETAILS"
        )

    @staticmethod
    async def update_job_status(
        session: AsyncSession, user: User, job_id: int, status: JobStatus
    ) -> Job:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job: raise ValueError("Job not found")
        if job.contractor_id != user.id: raise PermissionError("Unauthorized")

        return await JobService._apply_versioned_update(
            session, user, job,
            updates={"status": status},
            action_type=f"STATUS_CHANGE_{status.value}"
        )
        
    @staticmethod
    async def assign_homeowner(
        session: AsyncSession, user: User, job_id: int, homeowner_email: str
    ) -> Job:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job: raise ValueError("Job not found")
        if job.contractor_id != user.id: raise PermissionError("Unauthorized")

        # Verify Homeowner exists
        user_query = select(User).where(User.email == homeowner_email)
        user_result = await session.execute(user_query)
        homeowner = user_result.scalar_one_or_none()
        
        if not homeowner or homeowner.role != UserRole.HOMEOWNER:
             raise ValueError("Homeowner user not found")

        return await JobService._apply_versioned_update(
            session, user, job,
            updates={"homeowner_id": homeowner.id},
            action_type="ASSIGN_HOMEOWNER"
        )

    @staticmethod
    async def add_subtask(
        session: AsyncSession, user: User, job_id: int, description: str, cost: Decimal
    ) -> Job:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job: raise ValueError("Job not found")
        if job.contractor_id != user.id: raise PermissionError("Unauthorized")

        subtask = SubTask(
            description=description,
            cost=cost,
            job_id=job.id
        )
        session.add(subtask)
        await session.commit()
        # Refresh job to load the new subtask relationship
        await session.refresh(job, attribute_names=["subtasks"])
        return job

    # --- UNDO / REDO METHODS ---

    @staticmethod
    async def undo_last_change(session: AsyncSession, user: User, job_id: int) -> Job:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job: raise ValueError("Job not found")
        
        # Rule: Only contractors can Undo
        if user.role != UserRole.CONTRACTOR or job.contractor_id != user.id:
            raise PermissionError("Only the job owner can undo changes")

        if job.current_version <= 1:
            raise ValueError("Cannot undo initial creation")

        target_version = job.current_version - 1

        # 1. Fetch the target history (The state we want to go back to)
        query = select(JobHistory).where(
            JobHistory.job_id == job.id,
            JobHistory.version == target_version
        )
        result = await session.execute(query)
        history = result.scalar_one_or_none()

        if not history:
            raise ValueError(f"History for version {target_version} missing")

        # 2. Apply Snapshot
        snapshot = history.snapshot
        job.description = snapshot.get("description")
        job.location = snapshot.get("location")
        job.cost = Decimal(str(snapshot.get("cost"))) # Safety cast
        # Handle Enum conversion if necessary
        status_str = snapshot.get("status")
        # Assuming JobStatus(status_str) works, or simple assignment if string
        if isinstance(job.status, JobStatus):
             job.status = JobStatus(status_str) 
        else:
             job.status = status_str
        job.homeowner_id = snapshot.get("homeowner_id")

        # 3. Update Pointer (Do NOT delete history)
        job.current_version = target_version
        
        await session.commit()
        # Reload to ensure subtasks are loaded
        return await JobService.get_job_by_id(session, user, job.id)

    @staticmethod
    async def redo_last_change(session: AsyncSession, user: User, job_id: int) -> Job:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job: raise ValueError("Job not found")

        if user.role != UserRole.CONTRACTOR or job.contractor_id != user.id:
            raise PermissionError("Only the job owner can redo changes")

        target_version = job.current_version + 1

        # 1. Fetch the target history (The future state)
        query = select(JobHistory).where(
            JobHistory.job_id == job.id,
            JobHistory.version == target_version
        )
        result = await session.execute(query)
        history = result.scalar_one_or_none()

        if not history:
            raise ValueError("Nothing to redo")

        # 2. Apply Snapshot
        snapshot = history.snapshot
        job.description = snapshot.get("description")
        job.location = snapshot.get("location")
        job.cost = Decimal(str(snapshot.get("cost")))
        
        status_str = snapshot.get("status")
        if isinstance(job.status, JobStatus):
             job.status = JobStatus(status_str) 
        else:
             job.status = status_str
        job.homeowner_id = snapshot.get("homeowner_id")

        # 3. Update Pointer
        job.current_version = target_version
        
        await session.commit()
        # Reload to ensure subtasks are loaded
        return await JobService.get_job_by_id(session, user, job.id)

    # --- READ ---
    @staticmethod
    async def get_job_by_id(session: AsyncSession, user: User, job_id: int) -> Optional[Job]:
        query = select(Job).options(selectinload(Job.subtasks)).where(Job.id == job_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job: return None
            
        if job.contractor_id != user.id and job.homeowner_id != user.id:
            raise PermissionError("Not authorized to view this job")
            
        return job
    
    @staticmethod
    async def get_jobs_for_user(session: AsyncSession, user: User) -> List[Job]:
        if user.role == UserRole.CONTRACTOR:
            query = select(Job).options(selectinload(Job.subtasks)).where(Job.contractor_id == user.id).order_by(Job.id)
        else:
            query = select(Job).options(selectinload(Job.subtasks)).where(Job.homeowner_id == user.id).order_by(Job.id)
            
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_job_history(session: AsyncSession, user: User, job_id: int) -> List[JobHistory]:
        job = await JobService.get_job_by_id(session, user, job_id)
        if not job:
            raise ValueError("Job not found")
            
        # Permission: Both Contractor and Homeowner can view history
        # (Already covered by get_job_by_id check)

        query = select(JobHistory).where(
            JobHistory.job_id == job_id
        ).order_by(desc(JobHistory.version)) # Newest first
        
        result = await session.execute(query)
        return result.scalars().all()