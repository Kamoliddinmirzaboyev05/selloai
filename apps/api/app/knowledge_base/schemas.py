from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseEntryCreate(BaseModel):
    organization_id: str
    title: str = Field(min_length=2, max_length=180)
    content: str = Field(min_length=2, max_length=12000)
    is_active: bool = True


class KnowledgeBaseEntryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    content: str | None = Field(default=None, min_length=2, max_length=12000)
    is_active: bool | None = None


class KnowledgeBaseEntryRead(BaseModel):
    id: str
    organization_id: str
    title: str
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

