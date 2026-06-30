from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelegramInboundMessage:
    external_message_id: str
    customer_external_id: str
    chat_id: str
    text: str
    name: str | None
    username: str | None
    raw_payload: dict[str, Any]


def parse_telegram_update(payload: dict[str, Any]) -> TelegramInboundMessage | None:
    message = payload.get("message") or payload.get("edited_message")
    if not isinstance(message, dict):
        return None
    text = message.get("text")
    if not text:
        return None
    sender = message.get("from") or {}
    chat = message.get("chat") or {}
    sender_id = sender.get("id")
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    if sender_id is None or chat_id is None or message_id is None:
        return None
    first_name = sender.get("first_name")
    last_name = sender.get("last_name")
    name = " ".join(part for part in [first_name, last_name] if part) or None
    return TelegramInboundMessage(
        external_message_id=f"telegram:{chat_id}:{message_id}",
        customer_external_id=str(chat_id),
        chat_id=str(chat_id),
        text=text,
        name=name,
        username=sender.get("username"),
        raw_payload=payload,
    )

