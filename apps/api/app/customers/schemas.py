from datetime import datetime

from pydantic import BaseModel


class CustomerRead(BaseModel):
    id: str
    organization_id: str
    channel_id: str
    external_id: str
    name: str | None
    username: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

