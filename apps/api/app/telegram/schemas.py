from pydantic import BaseModel, Field

from app.channels.schemas import ChannelRead


class TelegramConnectRequest(BaseModel):
    organization_id: str
    bot_token: str = Field(min_length=20, max_length=160)


class TelegramConnectResponse(BaseModel):
    channel: ChannelRead
    webhook_path: str


class TelegramWebhookResponse(BaseModel):
    ok: bool
    created: bool = False
    reply_sent: bool = False

