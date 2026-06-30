import pytest

from app.ai.groq import GroqClient
from app.core.errors import AppError
from app.telegram.parser import parse_telegram_update


def test_telegram_parser_extracts_inbound_message():
    inbound = parse_telegram_update(
        {
            "message": {
                "message_id": 42,
                "text": "What is the price?",
                "chat": {"id": 1001},
                "from": {"id": 1001, "first_name": "Ada", "username": "ada"},
            }
        }
    )

    assert inbound is not None
    assert inbound.external_message_id == "telegram:1001:42"
    assert inbound.customer_external_id == "1001"
    assert inbound.name == "Ada"


async def test_groq_client_requires_api_key():
    client = GroqClient(api_key="", model="test-model")

    with pytest.raises(AppError) as exc:
        await client.chat_completion([{"role": "user", "content": "Hello"}])

    assert exc.value.code == "SERVICE_NOT_CONFIGURED"

