from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.channels.schemas import ChannelRead
from app.channels.services import list_channels
from app.core.database import get_session
from app.organizations.services import ensure_org_member
from app.users.models import User

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelRead])
async def list_channels_route(
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ChannelRead]:
    await ensure_org_member(session, current_user, organization_id)
    channels = await list_channels(session, organization_id)
    return [ChannelRead.model_validate(channel) for channel in channels]

