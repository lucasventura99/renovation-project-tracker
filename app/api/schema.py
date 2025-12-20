# app/api/schema.py
import strawberry
from app.api.resolvers.auth import AuthMutation

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "World"

# Merge AuthMutation into the root Mutation
@strawberry.type
class Mutation(AuthMutation):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)