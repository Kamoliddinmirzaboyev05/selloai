from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import IdMixin, TimestampMixin


class OrganizationSettings(IdMixin, TimestampMixin, Base):
    __tablename__ = "organization_settings"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"),
        unique=True,
        nullable=False,
    )
    ai_tone: Mapped[str] = mapped_column(String(80), default="friendly and concise", nullable=False)
    handoff_keywords: Mapped[str] = mapped_column(Text, default="human,agent,operator", nullable=False)
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

