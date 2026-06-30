from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import Conversation
from app.core.enums import ConversationStatus
from app.customers.models import Customer
from app.messages.services import utc_now


async def get_or_create_open_conversation(
    session: AsyncSession,
    *,
    organization_id: str,
    channel_id: str,
    customer_id: str,
) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.organization_id == organization_id,
            Conversation.channel_id == channel_id,
            Conversation.customer_id == customer_id,
            Conversation.status.in_(
                [
                    ConversationStatus.open,
                    ConversationStatus.ai_handling,
                    ConversationStatus.human_handoff,
                ]
            ),
        )
    )
    if conversation is None:
        conversation = Conversation(
            organization_id=organization_id,
            channel_id=channel_id,
            customer_id=customer_id,
            status=ConversationStatus.ai_handling,
            last_message_at=utc_now(),
        )
        session.add(conversation)
        await session.flush()
    return conversation


async def touch_conversation(conversation: Conversation) -> None:
    conversation.last_message_at = utc_now()


async def list_conversations(session: AsyncSession, organization_id: str) -> list[Conversation]:
    result = await session.scalars(
        select(Conversation)
        .where(Conversation.organization_id == organization_id)
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
    )
    return list(result)


async def get_conversation_for_org(
    session: AsyncSession,
    *,
    conversation_id: str,
    organization_id: str,
) -> Conversation | None:
    return await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == organization_id,
        )
    )


def conversation_customer_name(customer: Customer) -> str | None:
    return customer.name or customer.username or customer.external_id

