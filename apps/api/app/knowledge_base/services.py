from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge_base.models import KnowledgeBaseEntry


async def list_entries(session: AsyncSession, organization_id: str) -> list[KnowledgeBaseEntry]:
    result = await session.scalars(
        select(KnowledgeBaseEntry)
        .where(KnowledgeBaseEntry.organization_id == organization_id)
        .order_by(KnowledgeBaseEntry.updated_at.desc())
    )
    return list(result)


async def list_active_entries(session: AsyncSession, organization_id: str) -> list[KnowledgeBaseEntry]:
    result = await session.scalars(
        select(KnowledgeBaseEntry)
        .where(
            KnowledgeBaseEntry.organization_id == organization_id,
            KnowledgeBaseEntry.is_active.is_(True),
        )
        .order_by(KnowledgeBaseEntry.updated_at.desc())
    )
    return list(result)

