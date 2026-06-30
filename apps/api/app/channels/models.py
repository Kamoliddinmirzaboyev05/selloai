from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ChannelStatus, ChannelType
from app.core.models import IdMixin, TimestampMixin


class Channel(IdMixin, TimestampMixin, Base):
    __tablename__ = "channels"
    __table_args__ = (UniqueConstraint("organization_id", "type", "external_id"),)

    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    type: Mapped[ChannelType] = mapped_column(String(32), nullable=False)
    status: Mapped[ChannelStatus] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    organization = relationship("Organization", back_populates="channels")
    customers = relationship("Customer", back_populates="channel")

