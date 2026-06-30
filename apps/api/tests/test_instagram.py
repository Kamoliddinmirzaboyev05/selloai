import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from httpx import AsyncClient

from app.core.enums import ChannelStatus, ChannelType
from app.core.errors import AppError
from app.core.security import create_access_token, decode_access_token
from app.instagram.service import MetaPage
from app.oauth.crypto import decrypt_oauth_token, encrypt_oauth_token
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
    assert response.headers["content-type"].startswith("text/plain")
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


async def test_instagram_webhook_verification_rejects_missing_query_parameters(client: AsyncClient):
    response = await client.get("/api/v1/webhooks/instagram")

    assert response.status_code == 403
    assert response.json()["code"] == "META_WEBHOOK_VERIFICATION_FAILED"


async def test_instagram_webhook_verification_ignores_outer_token_whitespace(client: AsyncClient, monkeypatch):
    from app.instagram import router as instagram_router

    monkeypatch.setattr(instagram_router.settings, "meta_verify_token", " change-me ")
    response = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "change-me",
            "hub.challenge": "12345",
        },
    )

    assert response.status_code == 200
    assert response.text == "12345"


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


async def test_instagram_oauth_login_returns_authorization_url_for_json_clients(client: AsyncClient, monkeypatch):
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
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["authorization_url"].startswith("https://www.facebook.com/")
    assert "client_id=meta-app-id" in body["authorization_url"]
    assert "state=" in body["authorization_url"]


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
        headers={"Accept": "application/json"},
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
    assert "credentials" not in saved[0]


async def test_instagram_oauth_callback_redirects_browser_to_channels(client: AsyncClient, monkeypatch):
    from app.instagram import router as instagram_router
    from app.instagram import service as instagram_service

    monkeypatch.setattr(instagram_router.settings, "frontend_url", "https://sello.webportfolio.uz")
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
        return "short-token"

    async def fake_get_long_lived_token(self, access_token: str):
        return "long-user-token"

    async def fake_get_pages(self, access_token: str):
        return [MetaPage(id="page-1", name="Demo Page", access_token="page-token-1")]

    async def fake_get_instagram_business(self, page: MetaPage):
        return {"id": "ig-1", "username": "demo_shop"}

    monkeypatch.setattr(instagram_router.MetaService, "exchange_code", fake_exchange_code)
    monkeypatch.setattr(instagram_router.MetaService, "get_long_lived_token", fake_get_long_lived_token)
    monkeypatch.setattr(instagram_router.MetaService, "get_pages", fake_get_pages)
    monkeypatch.setattr(instagram_router.MetaService, "get_instagram_business", fake_get_instagram_business)

    response = await client.get(
        "/api/v1/integrations/instagram/oauth/callback",
        params={"code": "auth-code", "state": state},
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "https://sello.webportfolio.uz/dashboard/channels?instagram=connected"


async def test_instagram_oauth_callback_rejects_bad_state(client: AsyncClient):
    response = await client.get(
        "/api/v1/integrations/instagram/oauth/callback",
        params={"code": "auth-code", "state": "bad-state"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "META_OAUTH_INVALID_STATE"


async def test_instagram_save_channel_encrypts_meta_tokens_and_saves_account_metadata(monkeypatch):
    from app.instagram import service as instagram_service

    captured: dict[str, object] = {}

    async def fake_upsert_channel(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            id="channel-1",
            organization_id=kwargs["organization_id"],
            type=kwargs["channel_type"],
            status=kwargs["status"],
            display_name=kwargs["display_name"],
            external_id=kwargs["external_id"],
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr(instagram_service, "upsert_channel", fake_upsert_channel)

    await instagram_service.MetaService().save_channel(
        None,
        organization_id="org-1",
        page=MetaPage(id="page-1", name="Demo Page", access_token="page-token-secret"),
        instagram_business={"id": "ig-1", "username": "demo_shop", "name": "Demo Shop"},
        user_access_token="user-token-secret",
        connected_by_user_id="user-1",
    )

    credentials = captured["credentials"]
    metadata = captured["metadata"]
    serialized_credentials = json.dumps(credentials)
    assert "page-token-secret" not in serialized_credentials
    assert "user-token-secret" not in serialized_credentials
    assert decrypt_oauth_token(credentials["tokens"]["page_access_token"]) == "page-token-secret"
    assert decrypt_oauth_token(credentials["tokens"]["user_access_token"]) == "user-token-secret"
    assert credentials["provider"] == "meta"
    assert metadata["provider"] == "meta"
    assert metadata["provider_account_type"] == "instagram_business"
    assert metadata["facebook_page_id"] == "page-1"
    assert metadata["facebook_page_name"] == "Demo Page"
    assert metadata["instagram_business_account_id"] == "ig-1"
    assert metadata["instagram_username"] == "demo_shop"
    assert metadata["token_status"] == "active"
    assert captured["external_id"] == "ig-1"


async def test_instagram_refresh_channel_token_updates_encrypted_tokens(monkeypatch):
    from app.instagram import service as instagram_service

    class FakeSession:
        async def commit(self):
            return None

        async def refresh(self, _channel):
            return None

    async def fake_get_long_lived_token(self, access_token: str):
        assert access_token == "old-user-token"
        return "new-user-token"

    async def fake_get_pages(self, access_token: str):
        assert access_token == "new-user-token"
        return [MetaPage(id="page-1", name="Demo Page", access_token="new-page-token")]

    monkeypatch.setattr(instagram_service.MetaService, "get_long_lived_token", fake_get_long_lived_token)
    monkeypatch.setattr(instagram_service.MetaService, "get_pages", fake_get_pages)
    channel = SimpleNamespace(
        id="channel-1",
        organization_id="org-1",
        type=ChannelType.instagram,
        status=ChannelStatus.active,
        credentials={
            "provider": "meta",
            "tokens": {
                "page_access_token": encrypt_oauth_token("old-page-token"),
                "user_access_token": encrypt_oauth_token("old-user-token"),
            },
        },
        metadata_json={
            "provider": "meta",
            "facebook_page_id": "page-1",
            "token_expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
    )

    refreshed = await instagram_service.MetaService().refresh_channel_token(FakeSession(), channel)

    assert refreshed.status == ChannelStatus.active
    assert decrypt_oauth_token(refreshed.credentials["tokens"]["page_access_token"]) == "new-page-token"
    assert decrypt_oauth_token(refreshed.credentials["tokens"]["user_access_token"]) == "new-user-token"
    assert refreshed.metadata_json["token_status"] == "active"
    assert refreshed.metadata_json["last_token_refresh_at"]


async def test_instagram_refresh_channel_token_marks_reconnect_when_invalid(monkeypatch):
    from app.instagram import service as instagram_service

    class FakeSession:
        async def commit(self):
            return None

        async def refresh(self, _channel):
            return None

    async def fake_get_long_lived_token(self, access_token: str):
        raise AppError("Meta token is invalid.", "META_GRAPH_API_ERROR", 502)

    monkeypatch.setattr(instagram_service.MetaService, "get_long_lived_token", fake_get_long_lived_token)
    channel = SimpleNamespace(
        id="channel-1",
        organization_id="org-1",
        type=ChannelType.instagram,
        status=ChannelStatus.active,
        credentials={
            "provider": "meta",
            "tokens": {
                "page_access_token": encrypt_oauth_token("old-page-token"),
                "user_access_token": encrypt_oauth_token("old-user-token"),
            },
        },
        metadata_json={"provider": "meta", "facebook_page_id": "page-1"},
    )

    refreshed = await instagram_service.MetaService().refresh_channel_token(FakeSession(), channel)

    assert refreshed.status == ChannelStatus.needs_reconnect
    assert refreshed.metadata_json["token_status"] == "needs_reconnect"


async def test_instagram_refresh_channel_token_migrates_legacy_plaintext_credentials(monkeypatch):
    from app.instagram import service as instagram_service

    class FakeSession:
        async def commit(self):
            return None

        async def refresh(self, _channel):
            return None

    async def fake_get_long_lived_token(self, access_token: str):
        assert access_token == "legacy-user-token"
        return "new-user-token"

    async def fake_get_pages(self, access_token: str):
        return [MetaPage(id="page-1", name="Demo Page", access_token="new-page-token")]

    monkeypatch.setattr(instagram_service.MetaService, "get_long_lived_token", fake_get_long_lived_token)
    monkeypatch.setattr(instagram_service.MetaService, "get_pages", fake_get_pages)
    channel = SimpleNamespace(
        id="channel-1",
        organization_id="org-1",
        type=ChannelType.instagram,
        status=ChannelStatus.active,
        credentials={"page_access_token": "legacy-page-token", "user_access_token": "legacy-user-token"},
        metadata_json={"provider": "meta", "facebook_page_id": "page-1"},
    )

    refreshed = await instagram_service.MetaService().refresh_channel_token(FakeSession(), channel)

    serialized_credentials = json.dumps(refreshed.credentials)
    assert "legacy-user-token" not in serialized_credentials
    assert "new-user-token" not in serialized_credentials
    assert decrypt_oauth_token(refreshed.credentials["tokens"]["user_access_token"]) == "new-user-token"
