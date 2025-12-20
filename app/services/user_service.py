# app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password, create_access_token

async def create_user(session: AsyncSession, email: str, password: str, role: UserRole) -> User:
    # 1. Check if user already exists
    result = await session.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        # In a real app, you might want a custom exception here
        raise ValueError("Email already registered")

    # 2. Create new user instance
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        role=role
    )
    
    # 3. Persist to DB
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    # 1. Find user by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    # 2. Verify password
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
        
    return user

def generate_user_token(user: User) -> str:
    return create_access_token(subject=user.id)