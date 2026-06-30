from httpx import AsyncClient

from app.core.security import create_access_token, decode_access_token
from app.instagram.service import MetaPage
from tests.conftest import register_and_create_org


async def test_instagram_webhook_verification_returns_challenge(client: AsyncClient):
    response = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "change-me",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


async def test_instagram_webhook_verification_rejects_bad_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "bad",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "META_WEBHOOK_VERIFICATION_FAILED"


async def test_instagram_webhook_dispatches_dm_and_comment_events(client: AsyncClient):
    response = await client.post(
        "/api/v1/webhooks/instagram",
        json={
            "entry": [
                {
                    "messaging": [{"sender": {"id": "1"}, "message": {"text": "hi"}}],
                    "changes": [{"field": "comments", "value": {"text": "price?"}}],
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["dispatched"] == {"dm_events": 1, "comment_events": 1}


async def test_instagram_oauth_login_redirects_to_meta(client: AsyncClient, monkeypatch):
    from app.instagram import service as instagram_service

    monkeypatch.setattr(instagram_service.settings, "meta_app_id", "meta-app-id")
    monkeypatch.setattr(
        instagram_service.settings,
        "meta_oauth_callback_url",
        "https://selloapi.webportfolio.uz/auth/meta/callback",
    )
    token, organization_id = await register_and_create_org(client)

    response = await client.get(
        "/api/v1/integrations/instagram/oauth/login",
        params={"organization_id": organization_id},
        headers={"Authorization": f"Bearer {token}"},
        follow_redirects=False,
    )

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://www.facebook.com/")
    assert "client_id=meta-app-id" in location
    assert "redirect_uri=https%3A%2F%2Fselloapi.webportfolio.uz%2Fauth%2Fmeta%2Fcallback" in location
    assert "instagram_basic" in location
    assert "state=" in location


async def test_instagram_oauth_callback_exchanges_tokens_and_saves_channel(client: AsyncClient, monkeypatch):
    from app.instagram import router as instagram_router
    from app.instagram import service as instagram_service

    monkeypatch.setattr(instagram_service.settings, "meta_app_id", "meta-app-id")
    monkeypatch.setattr(instagram_service.settings, "meta_app_secret", "meta-app-secret")
    monkeypatch.setattr(
        instagram_service.settings,
        "meta_oauth_callback_url",
        "https://selloapi.webportfolio.uz/auth/meta/callback",
    )
    token, organization_id = await register_and_create_org(client)
    user_id = decode_access_token(token)["sub"]
    state = create_access_token(
        "meta_oauth",
        {"kind": "instagram_oauth", "organization_id": organization_id, "user_id": user_id},
    )

    async def fake_exchange_code(self, code: str):
        assert code == "auth-code"
        return "short-token"

    async def fake_get_long_lived_token(self, access_token: str):
        assert access_token == "short-token"
        return "long-user-token"

    async def fake_get_pages(self, access_token: str):
        assert access_token == "long-user-token"
        return [
            MetaPage(id="page-1", name="Demo Page", access_token="page-token-1"),
            MetaPage(id="page-2", name="No Instagram Page", access_token="page-token-2"),
        ]

    async def fake_get_instagram_business(self, page: MetaPage):
        if page.id == "page-1":
            return {"id": "ig-1", "username": "demo_shop"}
        return None

    monkeypatch.setattr(instagram_router.MetaService, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(instagram_router.MetaService, "get_long_lived_token", fake_get_long_lived_token)
    monkeypatch.setattr(instagram_router.MetaService, "get_pages", fake_get_pages)
    monkeypatch.setattr(instagram_router.MetaService, "get_instagram_business", fake_get_instagram_business)

    response = await client.get(
        "/api/v1/integrations/instagram/oauth/callback",
        params={"code": "auth-code", "state": state},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "connected"
    assert body["saved_channels"] == 1
    assert body["channels"][0]["external_id"] == "ig-1"
    assert body["channels"][0]["display_name"] == "demo_shop"

    channels = await client.get(
        "/api/v1/channels",
        params={"organization_id": organization_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert channels.status_code == 200
    saved = channels.json()
    assert len(saved) == 1
    assert saved[0]["type"] == "instagram"
    assert saved[0]["external_id"] == "ig-1"


async def test_instagram_oauth_callback_rejects_bad_state(client: AsyncClient):
    response = await client.get(
        "/api/v1/integrations/instagram/oauth/callback",
        params={"code": "auth-code", "state": "bad-state"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "META_OAUTH_INVALID_STATE"
