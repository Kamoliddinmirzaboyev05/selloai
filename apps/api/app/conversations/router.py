from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.channels.models import Channel
from app.conversations.schemas import ConversationMessagesRead, ConversationRead, ManualReplyRequest
from app.conversations.services import (
    conversation_customer_name,
    get_conversation_for_org,
    list_conversations,
    touch_conversation,
)
from app.core.database import get_session
from app.core.enums import MessageDirection, SenderType
from app.core.errors import AppError
from app.customers.models import Customer
from app.messages.schemas import MessageRead
from app.messages.services import create_message, list_messages
from app.organizations.services import ensure_org_member
from app.telegram.client import TelegramClient
from app.users.models import User

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def enrich_conversation(session: AsyncSession, conversation) -> ConversationRead:
    customer = await session.get(Customer, conversation.customer_id)
    channel = await session.get(Channel, conversation.channel_id)
    data = ConversationRead.model_validate(conversation).model_dump()
    data["customer_name"] = conversation_customer_name(customer) if customer else None
    data["channel_type"] = channel.type if channel else None
    return ConversationRead(**data)


@router.get("", response_model=list[ConversationRead])
async def list_conversations_route(
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationRead]:
    await ensure_org_member(session, current_user, organization_id)
    conversations = await list_conversations(session, organization_id)
    return [await enrich_conversation(session, conversation) for conversation in conversations]


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesRead)
async def get_conversation_messages(
    conversation_id: str,
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationMessagesRead:
    await ensure_org_member(session, current_user, organization_id)
    conversation = await get_conversation_for_org(
        session,
        conversation_id=conversation_id,
        organization_id=organization_id,
    )
    if conversation is None:
        raise AppError("Conversation not found.", "CONVERSATION_NOT_FOUND", 404)
    messages = await list_messages(session, conversation_id)
    return ConversationMessagesRead(
        conversation=await enrich_conversation(session, conversation),
        messages=[MessageRead.model_validate(message) for message in messages],
    )


@router.post("/{conversation_id}/manual-reply", response_model=MessageRead)
async def manual_reply(
    conversation_id: str,
    data: ManualReplyRequest,
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageRead:
    await ensure_org_member(session, current_user, organization_id)
    conversation = await get_conversation_for_org(
        session,
        conversation_id=conversation_id,
        organization_id=organization_id,
    )
    if conversation is None:
        raise AppError("Conversation not found.", "CONVERSATION_NOT_FOUND", 404)

    message, _created = await create_message(
        session,
        conversation_id=conversation.id,
        direction=MessageDirection.outbound,
        sender_type=SenderType.operator,
        body=data.body,
        raw_payload={"operator_user_id": current_user.id},
    )
    await touch_conversation(conversation)

    channel = await session.get(Channel, conversation.channel_id)
    customer = await session.get(Customer, conversation.customer_id)
    if channel and customer and channel.type == "telegram":
        await TelegramClient(channel.credentials["bot_token"]).send_message(customer.external_id, data.body)

    await session.commit()
    await session.refresh(message)
    return MessageRead.model_validate(message)

