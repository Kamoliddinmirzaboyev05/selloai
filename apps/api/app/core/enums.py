from enum import StrEnum


class OrganizationRole(StrEnum):
    owner = "owner"
    admin = "admin"
    operator = "operator"


class ChannelType(StrEnum):
    telegram = "telegram"
    instagram = "instagram"
    whatsapp = "whatsapp"
    website_chat = "website_chat"


class ChannelStatus(StrEnum):
    pending = "pending"
    active = "active"
    needs_reconnect = "needs_reconnect"
    disabled = "disabled"
    error = "error"


class ConversationStatus(StrEnum):
    open = "open"
    ai_handling = "ai_handling"
    human_handoff = "human_handoff"
    closed = "closed"


class MessageDirection(StrEnum):
    inbound = "inbound"
    outbound = "outbound"


class SenderType(StrEnum):
    customer = "customer"
    ai = "ai"
    operator = "operator"
    system = "system"
