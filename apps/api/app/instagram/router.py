import logging
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.channels.models import Channel
from app.channels.schemas import ChannelRead
from app.core.config import settings
from app.core.database import get_session
from app.core.enums import ChannelType
from app.core.errors import AppError
from app.instagram.handlers import dispatch_instagram_webhook
from app.instagram.schemas import (
    InstagramConnectionResponse,
    InstagramDisconnectResponse,
    InstagramManualTokenConnectRequest,
    InstagramOAuthCallbackResponse,
    InstagramOAuthLoginResponse,
)
from app.instagram.service import MetaService, _normalize_oauth_token
from app.oauth.audit import log_oauth_event
from app.oauth.schemas import OAuthProvider
from app.organizations.models import Organization
from app.organizations.services import ensure_org_member
from app.users.models import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["instagram"])


@router.post(
    "/integrations/instagram/token/connect",
    response_model=InstagramConnectionResponse,
    summary="Connect Instagram with a generated Meta access token",
    description="Verifies a generated Meta access token, discovers the connected Facebook Page and Instagram Business "
    "Account, stores encrypted credentials, and returns safe account identifiers only.",
)
async def instagram_manual_token_connect(
    data: InstagramManualTokenConnectRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InstagramConnectionResponse:
    await ensure_org_member(session, current_user, data.organization_id)
    connection = await MetaService().connect_with_access_token(
        session,
        organization_id=data.organization_id,
        access_token=data.access_token,
        connected_by_user_id=current_user.id,
    )
    instagram_username = connection.instagram_profile.get("username")
    return InstagramConnectionResponse(
        channel=ChannelRead.model_validate(connection.channel),
        instagram_username=instagram_username if isinstance(instagram_username, str) else None,
        instagram_account_id=connection.channel.external_id or connection.instagram_profile["id"],
        facebook_page_id=connection.page.id,
        facebook_page_name=connection.page.name,
    )


@router.post(
    "/integrations/instagram/channels/{channel_id}/disconnect",
    response_model=InstagramDisconnectResponse,
    summary="Disconnect an Instagram channel",
    description="Clears stored Meta credentials and marks the Instagram channel disabled.",
)
async def instagram_disconnect_channel(
    channel_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InstagramDisconnectResponse:
    channel = await session.get(Channel, channel_id)
    if channel is None or channel.type != ChannelType.instagram:
        raise AppError("Instagram channel not found.", "INSTAGRAM_CHANNEL_NOT_FOUND", 404)
    await ensure_org_member(session, current_user, channel.organization_id)
    disconnected = await MetaService().disconnect_channel(session, channel)
    return InstagramDisconnectResponse(channel=ChannelRead.model_validate(disconnected), status="disconnected")


@router.get(
    "/integrations/instagram/oauth/login",
    summary="Start Instagram OAuth",
    description="Generates a signed Meta OAuth state for the organization. Browser clients are redirected to Meta; "
    "JSON clients receive the Meta authorization URL.",
    responses={
        200: {"model": InstagramOAuthLoginResponse, "description": "Meta authorization URL for SPA clients."},
        307: {"description": "Redirect to Meta OAuth."},
    },
    response_model=None,
)
async def instagram_oauth_login(
    request: Request,
    organization_id: str = Query(description="Organization that will receive the Instagram channel connection."),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    await ensure_org_member(session, current_user, organization_id)
    oauth_url = MetaService().generate_oauth_url(organization_id=organization_id, user_id=current_user.id)
    if _wants_json(request):
        return InstagramOAuthLoginResponse(authorization_url=oauth_url)
    return RedirectResponse(oauth_url)


@router.get(
    "/integrations/instagram/oauth/callback",
    response_model=InstagramOAuthCallbackResponse,
    summary="Complete Instagram OAuth",
    description="Exchanges the Meta OAuth code, discovers linked Facebook Pages and Instagram Business Accounts, "
    "and saves active Instagram channel connections.",
)
async def instagram_oauth_callback(
    request: Request,
    code: str = Query(description="Authorization code returned by Meta OAuth."),
    state: str = Query(description="Signed OAuth state generated by Sello AI."),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = MetaService()
    state_payload = service.decode_oauth_state(state)
    organization_id = state_payload["organization_id"]
    user_id = state_payload["user_id"]
    log_oauth_event(
        "oauth_callback_received",
        provider=OAuthProvider.meta,
        organization_id=organization_id,
        user_id=user_id,
    )

    organization = await session.get(Organization, organization_id)
    user = await session.get(User, user_id)
    if organization is None or user is None:
        raise AppError("Meta OAuth state references an unknown organization.", "META_OAUTH_INVALID_STATE", 400)
    await ensure_org_member(session, user, organization_id)

    short_lived_token = await service.exchange_code(code)
    log_oauth_event("oauth_code_exchanged", provider=OAuthProvider.meta, organization_id=organization_id)
    long_lived_token = _normalize_oauth_token(await service.get_long_lived_token(short_lived_token))
    log_oauth_event("oauth_long_lived_token_created", provider=OAuthProvider.meta, organization_id=organization_id)
    pages = await service.get_pages(long_lived_token.access_token)
    log_oauth_event(
        "oauth_pages_fetched",
        provider=OAuthProvider.meta,
        organization_id=organization_id,
        page_count=len(pages),
    )
    channels = []
    for page in pages:
        instagram_business = await service.get_instagram_business(page)
        if instagram_business is None:
            continue
        log_oauth_event(
            "oauth_instagram_account_found",
            provider=OAuthProvider.meta,
            organization_id=organization_id,
            facebook_page_id=page.id,
            instagram_business_account_id=instagram_business.get("id"),
        )
        channel = await service.save_channel(
            session,
            organization_id=organization_id,
            page=page,
            instagram_business=instagram_business,
            user_access_token=long_lived_token.access_token,
            user_token_expires_at=long_lived_token.expires_at,
            connected_by_user_id=user_id,
        )
        log_oauth_event(
            "oauth_channel_saved",
            provider=OAuthProvider.meta,
            organization_id=organization_id,
            channel_id=channel.id,
            instagram_business_account_id=channel.external_id,
        )
        channels.append(ChannelRead.model_validate(channel))

    logger.info(
        "Completed Instagram OAuth",
        extra={"organization_id": organization_id, "saved_channels": len(channels), "pages": len(pages)},
    )
    result = InstagramOAuthCallbackResponse(
        status="connected" if channels else "no_instagram_business_account",
        saved_channels=len(channels),
        channels=channels,
    )
    if _wants_json(request):
        return result
    return RedirectResponse(f"{settings.browser_frontend_url}/dashboard/channels?instagram={result.status}")


@router.get(
    "/webhooks/instagram",
    response_class=PlainTextResponse,
    summary="Verify Instagram webhook",
    description="Implements Meta webhook verification by echoing the challenge when the verify token matches.",
)
async def verify_instagram_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    configured_token = settings.meta_verify_token.strip()
    received_token = hub_verify_token.strip() if hub_verify_token else ""
    token_matches = secrets.compare_digest(received_token, configured_token)
    if hub_mode == "subscribe" and hub_challenge is not None and token_matches:
        return hub_challenge
    raise AppError("Instagram webhook verification failed.", "META_WEBHOOK_VERIFICATION_FAILED", 403)


@router.post(
    "/webhooks/instagram",
    summary="Receive Instagram webhook events",
    description="Receives Instagram DM and comment webhook payloads and dispatches supported event skeletons.",
)
async def instagram_webhook(payload: dict) -> dict[str, object]:
    result = await dispatch_instagram_webhook(payload)
    return {"ok": True, "dispatched": result}


def _wants_json(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "application/json" in accept.lower()
