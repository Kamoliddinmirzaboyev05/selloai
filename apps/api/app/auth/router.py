from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest
from app.auth.services import authenticate_user, register_user
from app.core.database import get_session
from app.users.models import User
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    user, token = await register_user(session, data)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    user, token = await authenticate_user(session, data)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

