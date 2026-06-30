from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise AppError("Authentication is required.", "AUTH_REQUIRED", 401)
    payload = decode_access_token(credentials.credentials)
    user = await session.scalar(select(User).where(User.id == payload["sub"]))
    if user is None or not user.is_active:
        raise AppError("User not found.", "USER_NOT_FOUND", 401)
    return user

