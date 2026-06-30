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

2. Fill `API_JWT_SECRET`, `GROQ_API_KEY`, and `META_VERIFY_TOKEN` in `.env`.

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

## Instagram Skeleton

The Instagram module includes:

- Meta OAuth callback placeholder at `/api/v1/integrations/instagram/oauth/callback`
- Webhook verification at `/api/v1/webhooks/instagram`
- Webhook event dispatcher at `/api/v1/webhooks/instagram`
- DM handler skeleton
- Comment handler skeleton
- Meta Graph API client skeleton

These endpoints are intentionally structured for future production Meta OAuth, messaging, and comment reply implementation.

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
