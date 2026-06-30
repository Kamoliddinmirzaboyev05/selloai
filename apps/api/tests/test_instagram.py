from httpx import AsyncClient


async def test_instagram_webhook_verification_returns_challenge(client: AsyncClient):
    response = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "change-me",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


async def test_instagram_webhook_verification_rejects_bad_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "bad",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "META_WEBHOOK_VERIFICATION_FAILED"


async def test_instagram_webhook_dispatches_dm_and_comment_events(client: AsyncClient):
    response = await client.post(
        "/api/v1/webhooks/instagram",
        json={
            "entry": [
                {
                    "messaging": [{"sender": {"id": "1"}, "message": {"text": "hi"}}],
                    "changes": [{"field": "comments", "value": {"text": "price?"}}],
                }
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["dispatched"] == {"dm_events": 1, "comment_events": 1}

