from dataclasses import dataclass
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

    async def get_long_lived_token(self, access_token: str) -> str:
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
        return self._require_access_token(data, "META_OAUTH_LONG_LIVED_TOKEN_FAILED")

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

    async def save_channel(
        self,
        session: AsyncSession,
        *,
        organization_id: str,
        page: MetaPage,
        instagram_business: dict[str, Any],
        user_access_token: str,
        connected_by_user_id: str,
    ) -> Channel:
        instagram_id = instagram_business.get("id")
        if not isinstance(instagram_id, str):
            raise AppError("Instagram Business Account is missing an id.", "META_INSTAGRAM_ACCOUNT_INVALID", 502)
        username = instagram_business.get("username")
        display_name = username if isinstance(username, str) and username else page.name
        return await upsert_channel(
            session,
            organization_id=organization_id,
            channel_type=ChannelType.instagram,
            display_name=display_name,
            external_id=instagram_id,
            credentials={
                "page_access_token": page.access_token,
                "user_access_token": user_access_token,
            },
            metadata={
                "page_id": page.id,
                "page_name": page.name,
                "instagram_business_account": instagram_business,
                "connected_by_user_id": connected_by_user_id,
            },
            status=ChannelStatus.active,
        )

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

    def _ensure_oauth_login_settings(self) -> None:
        if not settings.meta_app_id or not settings.meta_oauth_callback_url:
            raise AppError("Meta OAuth is not configured.", "META_OAUTH_NOT_CONFIGURED", 503)

    @staticmethod
    def _require_access_token(data: dict[str, Any], code: str) -> str:
        access_token = data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AppError("Meta OAuth did not return an access token.", code, 502)
        return access_token
