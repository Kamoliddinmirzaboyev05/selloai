from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RegisterRequest
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.users.models import User


async def register_user(session: AsyncSession, data: RegisterRequest) -> tuple[User, str]:
    existing = await session.scalar(select(User).where(User.email == data.email.lower()))
    if existing is not None:
        raise AppError("A user with this email already exists.", "EMAIL_ALREADY_REGISTERED", 409)

    user = User(
        email=data.email.lower(),
        full_name=data.full_name.strip(),
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, create_access_token(user.id)


async def authenticate_user(session: AsyncSession, data: LoginRequest) -> tuple[User, str]:
    user = await session.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.hashed_password):
        raise AppError("Invalid email or password.", "INVALID_CREDENTIALS", 401)
    if not user.is_active:
        raise AppError("User account is disabled.", "USER_DISABLED", 403)
    return user, create_access_token(user.id)

