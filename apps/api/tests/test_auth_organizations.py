from httpx import AsyncClient


async def test_user_can_register_login_and_create_organization(client: AsyncClient):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "founder@example.com",
            "full_name": "Sello Founder",
            "password": "super-secret",
        },
    )

    assert register.status_code == 201
    token = register.json()["access_token"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "founder@example.com", "password": "super-secret"},
    )
    assert login.status_code == 200

    organization = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Sello Demo"},
    )
    assert organization.status_code == 201
    assert organization.json()["slug"] == "sello-demo"

    settings = await client.get(
        f"/api/v1/settings?organization_id={organization.json()['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert settings.status_code == 200
    assert settings.json()["auto_reply_enabled"] is True
