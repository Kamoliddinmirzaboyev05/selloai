from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.channels.router import router as channels_router
from app.conversations.router import router as conversations_router
from app.customers.router import router as customers_router
from app.instagram.router import router as instagram_router
from app.knowledge_base.router import router as knowledge_base_router
from app.organizations.router import router as organizations_router
from app.settings.router import router as settings_router
from app.telegram.router import router as telegram_router

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(settings_router)
api_router.include_router(channels_router)
api_router.include_router(customers_router)
api_router.include_router(conversations_router)
api_router.include_router(knowledge_base_router)
api_router.include_router(telegram_router)
api_router.include_router(instagram_router)
