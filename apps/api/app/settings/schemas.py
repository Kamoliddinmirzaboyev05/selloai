from pydantic import BaseModel, Field


class SettingsRead(BaseModel):
    id: str
    organization_id: str
    ai_tone: str
    handoff_keywords: str
    auto_reply_enabled: bool

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    organization_id: str
    ai_tone: str | None = Field(default=None, max_length=80)
    handoff_keywords: str | None = None
    auto_reply_enabled: bool | None = None

