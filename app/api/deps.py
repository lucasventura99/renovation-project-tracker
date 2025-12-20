# app/api/deps.py
from typing import Optional
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.config import settings
from app.core.security import ALGORITHM
from app.models.user import User

async def get_current_user(request: Request, db: AsyncSession) -> Optional[User]:
    """
    Extracts the token from the Authorization header, decodes it,
    and returns the User object. Returns None if invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    # Fetch user from DB
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()