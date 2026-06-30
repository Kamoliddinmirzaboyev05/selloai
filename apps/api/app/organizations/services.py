import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OrganizationRole
from app.organizations.models import Organization, OrganizationMember
from app.settings.models import OrganizationSettings
from app.users.models import User


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "organization"


async def create_organization(session: AsyncSession, user: User, name: str) -> Organization:
    base_slug = slugify(name)
    slug = base_slug
    counter = 2
    while await session.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base_slug}-{counter}"
        counter += 1

    organization = Organization(name=name.strip(), slug=slug)
    session.add(organization)
    await session.flush()
    session.add(
        OrganizationMember(
            organization_id=organization.id,
            user_id=user.id,
            role=OrganizationRole.owner,
        )
    )
    session.add(OrganizationSettings(organization_id=organization.id))
    await session.commit()
    await session.refresh(organization)
    return organization


async def list_user_organizations(session: AsyncSession, user: User) -> list[Organization]:
    result = await session.scalars(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)
        .order_by(Organization.created_at.asc())
    )
    return list(result)


async def ensure_org_member(session: AsyncSession, user: User, organization_id: str) -> OrganizationMember:
    membership = await session.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if membership is None:
        from app.core.errors import AppError

        raise AppError("Organization not found.", "ORGANIZATION_NOT_FOUND", 404)
    return membership

