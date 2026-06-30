from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError
from app.organizations.services import ensure_org_member
from app.settings.models import OrganizationSettings
from app.settings.schemas import SettingsRead, SettingsUpdate
from app.users.models import User

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
async def get_settings_route(
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationSettings:
    await ensure_org_member(session, current_user, organization_id)
    settings = await session.scalar(
        select(OrganizationSettings).where(OrganizationSettings.organization_id == organization_id)
    )
    if settings is None:
        raise AppError("Settings not found.", "SETTINGS_NOT_FOUND", 404)
    return settings


@router.patch("", response_model=SettingsRead)
async def update_settings_route(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationSettings:
    await ensure_org_member(session, current_user, data.organization_id)
    settings = await session.scalar(
        select(OrganizationSettings).where(OrganizationSettings.organization_id == data.organization_id)
    )
    if settings is None:
        raise AppError("Settings not found.", "SETTINGS_NOT_FOUND", 404)
    updates = data.model_dump(exclude_unset=True, exclude={"organization_id"})
    for key, value in updates.items():
        if value is not None:
            setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return settings

