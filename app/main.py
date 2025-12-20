# app/main.py
from fastapi import FastAPI, Depends, Request
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schema import schema
from app.db.session import get_db
from app.api.deps import get_current_user

async def get_context(request: Request, db: AsyncSession = Depends(get_db)):
    # Check for user on every request
    user = await get_current_user(request, db)
    return {
        "db": db,
        "user": user
    }

graphql_app = GraphQLRouter(schema, context_getter=get_context)

app = FastAPI(
    title="Renovation Project Tracker",
    version="1.0.0",
)

app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {"message": "Welcome to the Renovation Tracker API"}