from datetime import datetime

from pydantic import BaseModel

from app.core.enums import ChannelStatus, ChannelType


class ChannelRead(BaseModel):
    id: str
    organization_id: str
    type: ChannelType
    status: ChannelStatus
    display_name: str
    external_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

