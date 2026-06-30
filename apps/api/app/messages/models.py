from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import MessageDirection, SenderType
from app.core.models import IdMixin, TimestampMixin


class Message(IdMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("conversation_id", "external_id"),)

    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(String(16), nullable=False)
    sender_type: Mapped[SenderType] = mapped_column(String(24), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

