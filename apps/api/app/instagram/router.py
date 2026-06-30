import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.errors import AppError
from app.instagram.handlers import dispatch_instagram_webhook

logger = logging.getLogger(__name__)
router = APIRouter(tags=["instagram"])


@router.get("/integrations/instagram/oauth/callback")
async def instagram_oauth_callback(request: Request) -> dict[str, object]:
    params = dict(request.query_params)
    logger.info("Received Instagram OAuth callback placeholder", extra={"query_keys": list(params)})
    return {
        "status": "received",
        "message": "Meta OAuth token exchange is intentionally deferred for this MVP skeleton.",
        "received_query_keys": list(params.keys()),
    }


@router.get("/webhooks/instagram", response_class=PlainTextResponse)
async def verify_instagram_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> str:
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return hub_challenge
    raise AppError("Instagram webhook verification failed.", "META_WEBHOOK_VERIFICATION_FAILED", 403)


@router.post("/webhooks/instagram")
async def instagram_webhook(payload: dict) -> dict[str, object]:
    result = await dispatch_instagram_webhook(payload)
    return {"ok": True, "dispatched": result}

