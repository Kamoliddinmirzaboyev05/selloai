from pydantic import BaseModel

from app.channels.schemas import ChannelRead


class InstagramManualTokenConnectRequest(BaseModel):
    organization_id: str
    access_token: str


class InstagramOAuthLoginResponse(BaseModel):
    authorization_url: str


class InstagramOAuthCallbackResponse(BaseModel):
    status: str
    saved_channels: int
    channels: list[ChannelRead]


class InstagramConnectionResponse(BaseModel):
    channel: ChannelRead
    instagram_username: str | None
    instagram_account_id: str
    facebook_page_id: str
    facebook_page_name: str


class InstagramDisconnectResponse(BaseModel):
    channel: ChannelRead
    status: str
