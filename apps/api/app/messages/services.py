from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MessageDirection, SenderType
from app.messages.models import Message


async def create_message(
    session: AsyncSession,
    *,
    conversation_id: str,
    direction: MessageDirection,
    sender_type: SenderType,
    body: str,
    external_id: str | None = None,
    raw_payload: dict | None = None,
) -> tuple[Message, bool]:
    if external_id:
        existing = await session.scalar(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.external_id == external_id,
            )
        )
        if existing is not None:
            return existing, False

    message = Message(
        conversation_id=conversation_id,
        direction=direction,
        sender_type=sender_type,
        body=body,
        external_id=external_id,
        raw_payload=raw_payload or {},
    )
    session.add(message)
    return message, True


async def list_messages(session: AsyncSession, conversation_id: str, limit: int = 50) -> list[Message]:
    result = await session.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(list(result)))


def utc_now() -> datetime:
    return datetime.now(UTC)

