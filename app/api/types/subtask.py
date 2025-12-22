import strawberry

@strawberry.type
class SubTaskType:
    id: int
    description: str
    cost: float
    is_completed: bool