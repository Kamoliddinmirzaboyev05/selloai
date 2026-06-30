import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.services import generate_ai_reply
from app.auth.dependencies import get_current_user
from app.channels.schemas import ChannelRead
from app.channels.services import get_channel, upsert_channel
from app.conversations.services import get_or_create_open_conversation, touch_conversation
from app.core.database import get_session
from app.core.enums import ChannelStatus, ChannelType, MessageDirection, SenderType
from app.core.errors import AppError
from app.customers.services import upsert_customer
from app.messages.services import create_message
from app.organizations.models import Organization
from app.organizations.services import ensure_org_member
from app.settings.models import OrganizationSettings
from app.telegram.client import TelegramClient
from app.telegram.parser import parse_telegram_update
from app.telegram.schemas import TelegramConnectRequest, TelegramConnectResponse, TelegramWebhookResponse
from app.users.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram"])


@router.post("/channels/telegram/connect", response_model=TelegramConnectResponse)
async def connect_telegram_bot(
    data: TelegramConnectRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TelegramConnectResponse:
    await ensure_org_member(session, current_user, data.organization_id)
    bot = await TelegramClient(data.bot_token).get_me()
    channel = await upsert_channel(
        session,
        organization_id=data.organization_id,
        channel_type=ChannelType.telegram,
        display_name=bot.get("username") or bot.get("first_name") or "Telegram Bot",
        external_id=str(bot["id"]),
        credentials={"bot_token": data.bot_token},
        metadata={"bot": bot},
        status=ChannelStatus.active,
    )
    return TelegramConnectResponse(
        channel=ChannelRead.model_validate(channel),
        webhook_path=f"/api/v1/webhooks/telegram/{channel.id}",
    )


@router.post("/webhooks/telegram/{channel_id}", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    channel_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_session),
) -> TelegramWebhookResponse:
    channel = await get_channel(session, channel_id)
    if channel.type != ChannelType.telegram or channel.status != ChannelStatus.active:
        raise AppError("Telegram channel is not active.", "CHANNEL_NOT_ACTIVE", 404)

    inbound = parse_telegram_update(payload)
    if inbound is None:
        logger.info("Ignoring unsupported Telegram update", extra={"channel_id": channel_id})
        return TelegramWebhookResponse(ok=True)

    organization = await session.get(Organization, channel.organization_id)
    settings = await session.scalar(
        select(OrganizationSettings).where(
            OrganizationSettings.organization_id == channel.organization_id
        )
    )
    if organization is None or settings is None:
        raise AppError("Channel organization is not configured.", "ORGANIZATION_NOT_FOUND", 404)

    customer = await upsert_customer(
        session,
        organization_id=channel.organization_id,
        channel_id=channel.id,
        external_id=inbound.customer_external_id,
        name=inbound.name,
        username=inbound.username,
        metadata={"telegram_chat_id": inbound.chat_id},
    )
    conversation = await get_or_create_open_conversation(
        session,
        organization_id=channel.organization_id,
        channel_id=channel.id,
        customer_id=customer.id,
    )
    inbound_message, created = await create_message(
        session,
        conversation_id=conversation.id,
        direction=MessageDirection.inbound,
        sender_type=SenderType.customer,
        body=inbound.text,
        external_id=inbound.external_message_id,
        raw_payload=inbound.raw_payload,
    )
    await touch_conversation(conversation)
    await session.commit()
    await session.refresh(conversation)

    if not created:
        return TelegramWebhookResponse(ok=True, created=False, reply_sent=False)

    if not settings.auto_reply_enabled:
        return TelegramWebhookResponse(ok=True, created=True, reply_sent=False)

    reply = await generate_ai_reply(
        session,
        organization=organization,
        settings=settings,
        conversation_id=conversation.id,
        incoming_message=inbound_message.body,
    )
    outbound_message, _ = await create_message(
        session,
        conversation_id=conversation.id,
        direction=MessageDirection.outbound,
        sender_type=SenderType.ai,
        body=reply,
        raw_payload={"provider": "groq"},
    )
    await touch_conversation(conversation)
    await session.commit()
    await session.refresh(outbound_message)
    await TelegramClient(channel.credentials["bot_token"]).send_message(inbound.chat_id, reply)
    return TelegramWebhookResponse(ok=True, created=True, reply_sent=True)

