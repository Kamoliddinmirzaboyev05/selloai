# Sello AI

Sello AI is an AI sales assistant SaaS foundation for replying to customer messages across Telegram, Instagram, WhatsApp, and website chat. This MVP fully implements Telegram and includes production-shaped Instagram skeleton endpoints for Meta Graph API and webhooks.

## Stack

- Frontend: Next.js 15, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.12
- Database: PostgreSQL with SQLAlchemy and Alembic
- Auth: JWT
- AI: Groq API
- Queue/cache: Redis
- Deployment: Docker Compose

## Local Setup

1. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

2. Fill `API_JWT_SECRET`, `GROQ_API_KEY`, `META_VERIFY_TOKEN`, and Meta OAuth values in `.env` when testing Instagram.
   For production, also set `OAUTH_TOKEN_ENCRYPTION_KEY` so Meta tokens are encrypted at rest.

3. Start the stack:

   ```bash
   docker compose up --build
   ```

4. Open the dashboard at `http://localhost:3000`.

5. Open API docs at `http://localhost:8000/docs`.

## Backend Development

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests:

```bash
cd apps/api
pytest
```

## Frontend Development

```bash
npm install
npm run dev:web
```

## Telegram Setup

1. Create a bot with BotFather and copy the bot token.
2. Register and create an organization in Sello AI.
3. Connect the Telegram bot token from Dashboard > Channels.
4. Configure Telegram webhook to point at:

   ```text
   https://your-api-domain.com/api/v1/webhooks/telegram/{channel_id}
   ```

Incoming Telegram messages are persisted, enriched with organization knowledge base context, answered through Groq, saved, and sent back to Telegram.

## Instagram Integration

The Instagram module includes production Meta OAuth wiring for connecting Instagram Business Accounts through linked Facebook Pages:

- Meta OAuth start at `/api/v1/integrations/instagram/oauth/login`
- Meta OAuth callback at `/api/v1/integrations/instagram/oauth/callback`
- Webhook verification at `/api/v1/webhooks/instagram`
- Webhook event dispatcher at `/api/v1/webhooks/instagram`
- DM handler skeleton for incoming webhook events
- Comment handler skeleton for incoming webhook events
- Meta Graph API client methods for DM and comment replies

Meta access tokens are never returned to the frontend. Page and user tokens are encrypted before they are stored in
channel credentials. In production, generate an encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then set:

```bash
OAUTH_TOKEN_ENCRYPTION_KEY=<generated-key>
OAUTH_TOKEN_ENCRYPTION_KEY_VERSION=v1
OAUTH_TOKEN_REFRESH_WINDOW_DAYS=7
```

If Meta token refresh fails because a token is invalid or the Page is no longer available, Sello marks the channel as
`needs_reconnect`. The dashboard will show Reconnect Instagram and start the same OAuth flow again without exposing
tokens to the browser.

### Instagram Test Steps

1. In Meta Developers, set the OAuth redirect URI to:

   ```text
   https://selloapi.webportfolio.uz/auth/meta/callback
   ```

2. Set the Instagram webhook callback URL to:

   ```text
   https://selloapi.webportfolio.uz/webhooks/instagram
   ```

3. Configure environment variables:

   ```bash
   FRONTEND_URL=https://sello.webportfolio.uz
   API_CORS_ORIGINS=https://sello.webportfolio.uz
   META_APP_ID=your-meta-app-id
   META_APP_SECRET=your-meta-app-secret
   META_VERIFY_TOKEN=your-meta-webhook-verify-token
   META_OAUTH_CALLBACK_URL=https://selloapi.webportfolio.uz/auth/meta/callback
   INSTAGRAM_WEBHOOK_URL=https://selloapi.webportfolio.uz/webhooks/instagram
   OAUTH_TOKEN_ENCRYPTION_KEY=your-fernet-key
   ```

4. Log in to Sello AI, create or select an organization, then open Dashboard > Channels.
5. Click Connect Instagram on the Instagram channel card.
6. Complete Meta OAuth with a Facebook account that manages a Page linked to an Instagram Business Account.
7. After callback success, Sello AI returns to Dashboard > Channels and shows Instagram as connected.
8. If a token later becomes invalid, the channel status becomes `needs_reconnect`; click Reconnect Instagram to refresh
   the saved connection.

## Production Deployment

Production domains:

- Frontend: `https://sello.webportfolio.uz`
- Backend API: `https://selloapi.webportfolio.uz`
- Meta OAuth callback: `https://selloapi.webportfolio.uz/auth/meta/callback`
- Instagram webhook: `https://selloapi.webportfolio.uz/webhooks/instagram`

Production config files:

- `.env.production.example`
- `docker-compose.prod.yml`
- `deploy/nginx/sello.http.conf`
- `deploy/nginx/sello.conf`
- `docs/deployment/ubuntu-vps.md`

See [Ubuntu VPS deployment guide](docs/deployment/ubuntu-vps.md) for Docker Compose, Nginx, HTTPS, and Certbot steps.
