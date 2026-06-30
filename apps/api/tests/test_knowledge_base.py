from httpx import AsyncClient

from tests.conftest import register_and_create_org


async def test_user_can_manage_knowledge_base_entries(client: AsyncClient):
    token, organization_id = await register_and_create_org(client)

    created = await client.post(
        "/api/v1/knowledge-base",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_id": organization_id,
            "title": "Shipping",
            "content": "Orders ship within two business days.",
            "is_active": True,
        },
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]

    listed = await client.get(
        f"/api/v1/knowledge-base?organization_id={organization_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200
    assert listed.json()[0]["title"] == "Shipping"

    updated = await client.patch(
        f"/api/v1/knowledge-base/{entry_id}?organization_id={organization_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

