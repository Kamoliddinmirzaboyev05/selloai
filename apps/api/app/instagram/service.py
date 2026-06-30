from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.models import Channel
from app.channels.services import upsert_channel
from app.core.config import settings
from app.core.enums import ChannelStatus, ChannelType
from app.core.errors import AppError
from app.core.security import create_access_token, decode_access_token
from app.oauth.audit import log_oauth_event
from app.oauth.crypto import decrypt_oauth_token, encrypt_oauth_token
from app.oauth.schemas import OAuthAccessToken, OAuthProvider, ProviderAccountType

INSTAGRAM_OAUTH_SCOPES = (
    "instagram_basic",
    "instagram_manage_comments",
    "instagram_manage_messages",
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_metadata",
)


@dataclass(frozen=True)
class MetaPage:
    id: str
    name: str
    access_token: str


@dataclass(frozen=True)
class MetaInstagramConnection:
    channel: Channel
    page: MetaPage
    instagram_profile: dict[str, Any]


class MetaService:
    def __init__(self, api_version: str | None = None) -> None:
        self.api_version = api_version or settings.meta_graph_api_version
        self.graph_base_url = f"https://graph.facebook.com/{self.api_version}"
        self.oauth_base_url = f"https://www.facebook.com/{self.api_version}/dialog/oauth"

    def generate_oauth_url(self, *, organization_id: str, user_id: str) -> str:
        self._ensure_oauth_login_settings()
        state = create_access_token(
            "meta_oauth",
            {
                "kind": "instagram_oauth",
                "organization_id": organization_id,
                "user_id": user_id,
            },
        )
        query = urlencode(
            {
                "client_id": settings.meta_app_id,
                "redirect_uri": settings.meta_oauth_callback_url,
                "state": state,
                "scope": ",".join(INSTAGRAM_OAUTH_SCOPES),
                "response_type": "code",
            }
        )
        log_oauth_event(
            "oauth_login_started",
            provider=OAuthProvider.meta,
            organization_id=organization_id,
            user_id=user_id,
        )
        return f"{self.oauth_base_url}?{query}"

    def decode_oauth_state(self, state: str) -> dict[str, str]:
        try:
            payload = decode_access_token(state)
        except AppError as exc:
            raise AppError("Invalid Meta OAuth state.", "META_OAUTH_INVALID_STATE", 400) from exc
        if payload.get("sub") != "meta_oauth" or payload.get("kind") != "instagram_oauth":
            raise AppError("Invalid Meta OAuth state.", "META_OAUTH_INVALID_STATE", 400)
        organization_id = payload.get("organization_id")
        user_id = payload.get("user_id")
        if not isinstance(organization_id, str) or not isinstance(user_id, str):
            raise AppError("Invalid Meta OAuth state.", "META_OAUTH_INVALID_STATE", 400)
        return {"organization_id": organization_id, "user_id": user_id}

    async def exchange_code(self, code: str) -> str:
        self._ensure_oauth_settings()
        data = await self._get_json(
            "/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": settings.meta_oauth_callback_url,
                "code": code,
            },
        )
        return self._require_access_token(data, "META_OAUTH_CODE_EXCHANGE_FAILED")

    async def get_long_lived_token(self, access_token: str) -> OAuthAccessToken:
        self._ensure_oauth_settings()
        data = await self._get_json(
            "/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": access_token,
            },
        )
        return self._require_oauth_token(data, "META_OAUTH_LONG_LIVED_TOKEN_FAILED")

    async def get_pages(self, access_token: str) -> list[MetaPage]:
        data = await self._get_json(
            "/me/accounts",
            params={
                "access_token": access_token,
                "fields": "id,name,access_token",
            },
        )
        pages = []
        for item in data.get("data", []):
            page_id = item.get("id")
            name = item.get("name")
            page_token = item.get("access_token")
            if isinstance(page_id, str) and isinstance(name, str) and isinstance(page_token, str):
                pages.append(MetaPage(id=page_id, name=name, access_token=page_token))
        return pages

    async def debug_token(self, access_token: str) -> dict[str, Any]:
        self._ensure_meta_app_settings()
        data = await self._get_json(
            "/debug_token",
            params={
                "input_token": access_token,
                "access_token": f"{settings.meta_app_id}|{settings.meta_app_secret}",
            },
        )
        token_data = data.get("data")
        if not isinstance(token_data, dict):
            raise AppError("Meta token debug returned an invalid response.", "META_TOKEN_DEBUG_INVALID_RESPONSE", 502)
        return token_data

    async def get_instagram_business(self, page: MetaPage) -> dict[str, Any] | None:
        data = await self._get_json(
            f"/{page.id}",
            params={
                "access_token": page.access_token,
                "fields": "instagram_business_account{id,username,name}",
            },
        )
        instagram_business = data.get("instagram_business_account")
        return instagram_business if isinstance(instagram_business, dict) else None

    async def get_instagram_profile(self, instagram_account_id: str, page_access_token: str) -> dict[str, Any]:
        data = await self._get_json(
            f"/{instagram_account_id}",
            params={
                "access_token": page_access_token,
                "fields": "id,username,name,profile_picture_url",
            },
        )
        if not isinstance(data.get("id"), str):
            raise AppError("Instagram profile response is missing an id.", "META_INSTAGRAM_PROFILE_INVALID", 502)
        return data

    async def connect_with_access_token(
        self,
        session: AsyncSession,
        *,
        organization_id: str,
        access_token: str,
        connected_by_user_id: str,
    ) -> MetaInstagramConnection:
        token_debug = await self.debug_token(access_token)
        if token_debug.get("is_valid") is not True:
            raise AppError("Meta access token is invalid.", "META_ACCESS_TOKEN_INVALID", 401)

        pages = await self.get_pages(access_token)
        if not pages:
            raise AppError("No Facebook Pages were found for this token.", "META_PAGE_NOT_FOUND_FOR_TOKEN", 400)

        for page in pages:
            instagram_business = await self.get_instagram_business(page)
            if instagram_business is None:
                continue
            instagram_id = instagram_business.get("id")
            if not isinstance(instagram_id, str):
                continue
            instagram_profile = await self.get_instagram_profile(instagram_id, page.access_token)
            channel = await self.save_channel(
                session,
                organization_id=organization_id,
                page=page,
                instagram_business={**instagram_business, **instagram_profile},
                user_access_token=access_token,
                connected_by_user_id=connected_by_user_id,
            )
            log_oauth_event(
                "manual_instagram_token_connected",
                provider=OAuthProvider.meta,
                organization_id=organization_id,
                channel_id=channel.id,
                facebook_page_id=page.id,
                instagram_business_account_id=instagram_id,
            )
            return MetaInstagramConnection(channel=channel, page=page, instagram_profile=instagram_profile)

        raise AppError(
            "No Instagram Business Account is linked to the Facebook Pages available to this token.",
            "META_INSTAGRAM_ACCOUNT_NOT_FOUND_FOR_TOKEN",
            400,
        )

    async def save_channel(
        self,
        session: AsyncSession,
        *,
        organization_id: str,
        page: MetaPage,
        instagram_business: dict[str, Any],
        user_access_token: str,
        connected_by_user_id: str,
        user_token_expires_at: datetime | None = None,
    ) -> Channel:
        instagram_id = instagram_business.get("id")
        if not isinstance(instagram_id, str):
            raise AppError("Instagram Business Account is missing an id.", "META_INSTAGRAM_ACCOUNT_INVALID", 502)
        username = instagram_business.get("username")
        display_name = username if isinstance(username, str) and username else page.name
        token_expires_at = user_token_expires_at or _default_meta_token_expires_at()
        return await upsert_channel(
            session,
            organization_id=organization_id,
            channel_type=ChannelType.instagram,
            display_name=display_name,
            external_id=instagram_id,
            credentials={
                "provider": OAuthProvider.meta,
                "tokens": {
                    "page_access_token": encrypt_oauth_token(page.access_token),
                    "user_access_token": encrypt_oauth_token(user_access_token),
                },
            },
            metadata={
                "provider": OAuthProvider.meta,
                "provider_account_type": ProviderAccountType.instagram_business,
                "facebook_page_id": page.id,
                "facebook_page_name": page.name,
                "instagram_business_account_id": instagram_id,
                "instagram_username": username,
                "connected_by_user_id": connected_by_user_id,
                "token_status": "active",
                "token_expires_at": token_expires_at.isoformat(),
                "last_token_refresh_at": None,
                "instagram_business_account": instagram_business,
            },
            status=ChannelStatus.active,
        )

    async def disconnect_channel(self, session: AsyncSession, channel: Channel) -> Channel:
        if channel.type != ChannelType.instagram:
            raise AppError("Channel is not an Instagram channel.", "CHANNEL_TYPE_INVALID", 400)
        metadata = dict(channel.metadata_json)
        metadata.update(
            {
                "token_status": "disconnected",
                "disconnected_at": datetime.now(UTC).isoformat(),
            }
        )
        channel.credentials = {}
        channel.metadata_json = metadata
        channel.status = ChannelStatus.disabled
        await session.commit()
        await session.refresh(channel)
        log_oauth_event(
            "instagram_channel_disconnected",
            provider=OAuthProvider.meta,
            organization_id=channel.organization_id,
            channel_id=channel.id,
        )
        return channel

    async def ensure_fresh_channel_tokens(self, session: AsyncSession, channel: Channel) -> Channel:
        if not self._is_token_refresh_due(channel):
            return channel
        return await self.refresh_channel_token(session, channel)

    async def refresh_channel_token(self, session: AsyncSession, channel: Channel) -> Channel:
        if channel.type != ChannelType.instagram:
            raise AppError("Channel is not an Instagram channel.", "CHANNEL_TYPE_INVALID", 400)
        try:
            user_token = _read_stored_oauth_token(channel.credentials, "user_access_token")
            refreshed_token = _normalize_oauth_token(await self.get_long_lived_token(user_token))
            pages = await self.get_pages(refreshed_token.access_token)
            page_id = channel.metadata_json.get("facebook_page_id") or channel.metadata_json.get("page_id")
            page = next((item for item in pages if item.id == page_id), None)
            if page is None:
                raise AppError("Connected Facebook Page is no longer available.", "META_PAGE_RECONNECT_REQUIRED", 409)

            channel.credentials = {
                "provider": OAuthProvider.meta,
                "tokens": {
                    "page_access_token": encrypt_oauth_token(page.access_token),
                    "user_access_token": encrypt_oauth_token(refreshed_token.access_token),
                },
            }
            metadata = dict(channel.metadata_json)
            metadata.update(
                {
                    "provider": OAuthProvider.meta,
                    "facebook_page_id": page.id,
                    "facebook_page_name": page.name,
                    "token_status": "active",
                    "token_expires_at": (refreshed_token.expires_at or _default_meta_token_expires_at()).isoformat(),
                    "last_token_refresh_at": datetime.now(UTC).isoformat(),
                    "last_token_refresh_error": None,
                }
            )
            channel.metadata_json = metadata
            channel.status = ChannelStatus.active
            await session.commit()
            await session.refresh(channel)
            log_oauth_event(
                "oauth_token_refresh_succeeded",
                provider=OAuthProvider.meta,
                organization_id=channel.organization_id,
                channel_id=channel.id,
                facebook_page_id=page.id,
            )
            return channel
        except AppError as exc:
            if exc.code in {
                "META_GRAPH_API_ERROR",
                "META_OAUTH_LONG_LIVED_TOKEN_FAILED",
                "META_PAGE_RECONNECT_REQUIRED",
                "OAUTH_TOKEN_DECRYPT_FAILED",
                "OAUTH_TOKEN_MISSING",
            }:
                return await self._mark_reconnect_required(session, channel, exc)
            raise

    async def _mark_reconnect_required(self, session: AsyncSession, channel: Channel, exc: AppError) -> Channel:
        metadata = dict(channel.metadata_json)
        metadata.update(
            {
                "token_status": "needs_reconnect",
                "last_token_refresh_error": exc.code,
                "last_token_refresh_error_at": datetime.now(UTC).isoformat(),
            }
        )
        channel.metadata_json = metadata
        channel.status = ChannelStatus.needs_reconnect
        await session.commit()
        await session.refresh(channel)
        log_oauth_event(
            "oauth_reconnect_required",
            provider=OAuthProvider.meta,
            organization_id=channel.organization_id,
            channel_id=channel.id,
            reason=exc.code,
        )
        return channel

    async def _get_json(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.graph_base_url}{path}", params=params)
        if response.status_code >= 400:
            raise AppError("Meta Graph API request failed.", "META_GRAPH_API_ERROR", 502)
        data = response.json()
        if not isinstance(data, dict):
            raise AppError("Meta Graph API returned an invalid response.", "META_GRAPH_API_INVALID_RESPONSE", 502)
        return data

    def _ensure_oauth_settings(self) -> None:
        if not settings.meta_app_id or not settings.meta_app_secret or not settings.meta_oauth_callback_url:
            raise AppError("Meta OAuth is not configured.", "META_OAUTH_NOT_CONFIGURED", 503)

    def _ensure_meta_app_settings(self) -> None:
        if not settings.meta_app_id or not settings.meta_app_secret:
            raise AppError("Meta app credentials are not configured.", "META_APP_NOT_CONFIGURED", 503)

    def _ensure_oauth_login_settings(self) -> None:
        if not settings.meta_app_id or not settings.meta_oauth_callback_url:
            raise AppError("Meta OAuth is not configured.", "META_OAUTH_NOT_CONFIGURED", 503)

    def _is_token_refresh_due(self, channel: Channel) -> bool:
        expires_at = _parse_datetime(channel.metadata_json.get("token_expires_at"))
        if expires_at is None:
            return True
        refresh_at = expires_at - timedelta(days=settings.oauth_token_refresh_window_days)
        return datetime.now(UTC) >= refresh_at

    @staticmethod
    def _require_access_token(data: dict[str, Any], code: str) -> str:
        access_token = data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AppError("Meta OAuth did not return an access token.", code, 502)
        return access_token

    @staticmethod
    def _require_oauth_token(data: dict[str, Any], code: str) -> OAuthAccessToken:
        access_token = MetaService._require_access_token(data, code)
        expires_in = data.get("expires_in")
        expires_at = None
        if isinstance(expires_in, int) and expires_in > 0:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        return OAuthAccessToken(access_token=access_token, expires_at=expires_at)


def _normalize_oauth_token(token: str | OAuthAccessToken) -> OAuthAccessToken:
    if isinstance(token, OAuthAccessToken):
        return token
    return OAuthAccessToken(access_token=token, expires_at=_default_meta_token_expires_at())


def _default_meta_token_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=60)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _read_stored_oauth_token(credentials: dict[str, Any], token_name: str) -> str:
    token_envelope = credentials.get("tokens", {}).get(token_name)
    if isinstance(token_envelope, dict):
        return decrypt_oauth_token(token_envelope)
    legacy_token = credentials.get(token_name)
    if isinstance(legacy_token, str) and legacy_token:
        return legacy_token
    raise AppError("OAuth token is missing from channel credentials.", "OAUTH_TOKEN_MISSING", 409)
