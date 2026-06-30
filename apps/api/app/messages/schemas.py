from datetime import datetime

from pydantic import BaseModel

from app.core.enums import MessageDirection, SenderType


class MessageRead(BaseModel):
    id: str
    conversation_id: str
    direction: MessageDirection
    sender_type: SenderType
    body: str
    external_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

