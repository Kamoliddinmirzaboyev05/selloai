from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError
from app.knowledge_base.models import KnowledgeBaseEntry
from app.knowledge_base.schemas import (
    KnowledgeBaseEntryCreate,
    KnowledgeBaseEntryRead,
    KnowledgeBaseEntryUpdate,
)
from app.knowledge_base.services import list_entries
from app.organizations.services import ensure_org_member
from app.users.models import User

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get("", response_model=list[KnowledgeBaseEntryRead])
async def list_knowledge_base(
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[KnowledgeBaseEntryRead]:
    await ensure_org_member(session, current_user, organization_id)
    entries = await list_entries(session, organization_id)
    return [KnowledgeBaseEntryRead.model_validate(entry) for entry in entries]


@router.post("", response_model=KnowledgeBaseEntryRead, status_code=201)
async def create_knowledge_base_entry(
    data: KnowledgeBaseEntryCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> KnowledgeBaseEntry:
    await ensure_org_member(session, current_user, data.organization_id)
    entry = KnowledgeBaseEntry(**data.model_dump())
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=KnowledgeBaseEntryRead)
async def update_knowledge_base_entry(
    entry_id: str,
    data: KnowledgeBaseEntryUpdate,
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> KnowledgeBaseEntry:
    await ensure_org_member(session, current_user, organization_id)
    entry = await session.get(KnowledgeBaseEntry, entry_id)
    if entry is None or entry.organization_id != organization_id:
        raise AppError("Knowledge base entry not found.", "KNOWLEDGE_BASE_ENTRY_NOT_FOUND", 404)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
async def delete_knowledge_base_entry(
    entry_id: str,
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await ensure_org_member(session, current_user, organization_id)
    entry = await session.get(KnowledgeBaseEntry, entry_id)
    if entry is None or entry.organization_id != organization_id:
        raise AppError("Knowledge base entry not found.", "KNOWLEDGE_BASE_ENTRY_NOT_FOUND", 404)
    await session.delete(entry)
    await session.commit()

