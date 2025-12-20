# app/api/schema.py
import strawberry
from app.api.resolvers.auth import AuthMutation
from app.api.resolvers.job import JobQuery, JobMutation

@strawberry.type
class Query(JobQuery):
    @strawberry.field
    def hello(self) -> str:
        return "World"

@strawberry.type
class Mutation(AuthMutation, JobMutation):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
