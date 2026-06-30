from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import ChannelType, ConversationStatus
from app.messages.schemas import MessageRead


class ConversationRead(BaseModel):
    id: str
    organization_id: str
    channel_id: str
    customer_id: str
    status: ConversationStatus
    assigned_user_id: str | None
    last_message_at: datetime | None
    customer_name: str | None = None
    channel_type: ChannelType | None = None

    model_config = {"from_attributes": True}


class ConversationMessagesRead(BaseModel):
    conversation: ConversationRead
    messages: list[MessageRead]


class ManualReplyRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)

