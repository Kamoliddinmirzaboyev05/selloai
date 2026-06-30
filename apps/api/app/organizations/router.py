from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationCreate, OrganizationRead
from app.organizations.services import create_organization, ensure_org_member, list_user_organizations
from app.users.models import User

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=201)
async def create_org(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationRead:
    organization = await create_organization(session, current_user, data.name)
    return OrganizationRead.model_validate(organization)


@router.get("", response_model=list[OrganizationRead])
async def list_orgs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[OrganizationRead]:
    organizations = await list_user_organizations(session, current_user)
    return [OrganizationRead.model_validate(organization) for organization in organizations]


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_org(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OrganizationRead:
    await ensure_org_member(session, current_user, organization_id)
    organization = await session.get(Organization, organization_id)
    if organization is None:
        raise AppError("Organization not found.", "ORGANIZATION_NOT_FOUND", 404)
    return OrganizationRead.model_validate(organization)
