from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.models import Channel
from app.core.enums import ChannelStatus, ChannelType
from app.core.errors import AppError


async def get_channel(session: AsyncSession, channel_id: str) -> Channel:
    channel = await session.get(Channel, channel_id)
    if channel is None:
        raise AppError("Channel not found.", "CHANNEL_NOT_FOUND", 404)
    return channel


async def list_channels(session: AsyncSession, organization_id: str) -> list[Channel]:
    result = await session.scalars(
        select(Channel)
        .where(Channel.organization_id == organization_id)
        .order_by(Channel.created_at.asc())
    )
    return list(result)


async def upsert_channel(
    session: AsyncSession,
    *,
    organization_id: str,
    channel_type: ChannelType,
    display_name: str,
    external_id: str | None,
    credentials: dict,
    metadata: dict | None = None,
    status: ChannelStatus = ChannelStatus.active,
) -> Channel:
    channel = await session.scalar(
        select(Channel).where(
            Channel.organization_id == organization_id,
            Channel.type == channel_type,
            Channel.external_id == external_id,
        )
    )
    if channel is None:
        channel = Channel(
            organization_id=organization_id,
            type=channel_type,
            display_name=display_name,
            external_id=external_id,
            credentials=credentials,
            metadata_json=metadata or {},
            status=status,
        )
        session.add(channel)
    else:
        channel.display_name = display_name
        channel.credentials = credentials
        channel.metadata_json = metadata or {}
        channel.status = status
    await session.commit()
    await session.refresh(channel)
    return channel

