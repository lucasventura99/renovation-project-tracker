import strawberry
from typing import Optional, List
from datetime import datetime
import json
from app.api.types.subtask import SubTaskType

@strawberry.type
class JobHistoryType:
    id: int
    version: int
    action_type: str
    changed_at: datetime
    
    @strawberry.field
    def snapshot_json(self) -> str:
        # Safety check: if snapshot is None (shouldn't happen), return empty dict
        return json.dumps(self.snapshot) if self.snapshot else "{}"

@strawberry.type
class JobType:
    id: int
    description: str
    location: str
    cost: float
    status: str
    current_version: int 
    created_at: datetime
    updated_at: datetime
    subtasks: List[SubTaskType]
    
    @strawberry.field
    async def history(self, info) -> List[JobHistoryType]:
        from app.services.job_service import JobService 

        user = info.context.get("user") 
        db = info.context.get("db")
        
        # Safety check
        if not db or not user:
            return []
            
        return await JobService.get_job_history(db, user, self.id)