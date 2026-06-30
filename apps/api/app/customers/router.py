from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_session
from app.customers.schemas import CustomerRead
from app.customers.services import list_customers
from app.organizations.services import ensure_org_member
from app.users.models import User

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
async def list_customers_route(
    organization_id: str = Query(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CustomerRead]:
    await ensure_org_member(session, current_user, organization_id)
    customers = await list_customers(session, organization_id)
    return [CustomerRead.model_validate(customer) for customer in customers]

