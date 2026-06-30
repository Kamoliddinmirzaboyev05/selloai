from pydantic import BaseModel

from app.channels.schemas import ChannelRead


class InstagramOAuthCallbackResponse(BaseModel):
    status: str
    saved_channels: int
    channels: list[ChannelRead]

