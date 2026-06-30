from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.customers.models import Customer


async def upsert_customer(
    session: AsyncSession,
    *,
    organization_id: str,
    channel_id: str,
    external_id: str,
    name: str | None,
    username: str | None,
    metadata: dict | None = None,
) -> Customer:
    customer = await session.scalar(
        select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.channel_id == channel_id,
            Customer.external_id == external_id,
        )
    )
    if customer is None:
        customer = Customer(
            organization_id=organization_id,
            channel_id=channel_id,
            external_id=external_id,
            name=name,
            username=username,
            metadata_json=metadata or {},
        )
        session.add(customer)
    else:
        customer.name = name or customer.name
        customer.username = username or customer.username
        customer.metadata_json = metadata or customer.metadata_json
    await session.flush()
    return customer


async def list_customers(session: AsyncSession, organization_id: str) -> list[Customer]:
    result = await session.scalars(
        select(Customer)
        .where(Customer.organization_id == organization_id)
        .order_by(Customer.updated_at.desc())
    )
    return list(result)

