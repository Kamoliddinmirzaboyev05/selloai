from pydantic import BaseModel

from app.channels.schemas import ChannelRead


class InstagramOAuthLoginResponse(BaseModel):
    authorization_url: str


class InstagramOAuthCallbackResponse(BaseModel):
    status: str
    saved_channels: int
    channels: list[ChannelRead]
