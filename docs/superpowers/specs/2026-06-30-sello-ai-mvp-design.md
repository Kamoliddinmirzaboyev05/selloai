# Sello AI MVP Design

Date: 2026-06-30

## Goal

Build Sello AI, a production-ready MVP SaaS foundation for an AI sales assistant that replies to customer messages across business messaging channels. The MVP fully supports Telegram and includes an Instagram integration skeleton for Meta Graph API and webhooks.

## Scope

The MVP includes:

- User registration and login with JWT authentication.
- Organization creation and membership.
- Telegram bot token connection.
- Telegram webhook ingestion.
- PostgreSQL persistence for customers, conversations, and messages.
- AI replies through Groq using organization knowledge base entries as context.
- Admin dashboard for conversations, customers, knowledge base, channels, and settings.
- Human operator manual replies.
- Instagram skeleton with Meta OAuth callback placeholder, webhook verification, DM event handler skeleton, comment event handler skeleton, and Meta Graph API client skeleton.
- Docker Compose deployment for frontend, backend, PostgreSQL, and Redis.

The MVP excludes billing, WhatsApp production integration, website chat production integration, multi-role permissions beyond owner/operator/admin basics, and advanced analytics.

## Architecture

Use a monorepo:

```text
apps/
  web/      Next.js 15, TypeScript, Tailwind CSS
  api/      FastAPI, Python 3.12, SQLAlchemy, Alembic
packages/
  shared/   shared TypeScript DTOs and constants
```

The backend is a modular monolith. Each domain module owns its router, schemas, service layer, and persistence interactions. Channel integrations share common conversation, customer, and message services so future WhatsApp and website chat adapters can reuse the same core pipeline.

The frontend is a dashboard application with authenticated routes. It calls the API with bearer tokens and uses shared DTO definitions from `packages/shared` where practical.

## Backend Modules

- `auth`: password hashing, registration, login, JWT creation, current-user dependency.
- `users`: user profile and membership lookup.
- `organizations`: organization CRUD and membership creation.
- `channels`: connected channel records and status.
- `telegram`: bot token storage, webhook registration helper, webhook receiver, Telegram send-message client.
- `instagram`: OAuth callback placeholder, webhook verification endpoint, DM/comment handler skeletons, Meta Graph API client skeleton.
- `customers`: customer identity records per organization/channel.
- `conversations`: threaded customer conversations.
- `messages`: inbound, AI outbound, and human outbound messages.
- `knowledge_base`: organization knowledge snippets used by AI.
- `ai`: Groq client, prompt builder, answer generation service.
- `handoff`: conversation status changes and manual reply path.
- `settings`: organization-level settings.
- `core`: config, database, security, logging, errors.

## Data Model

Core entities:

- `users`: email, hashed password, name, active status.
- `organizations`: name and slug.
- `organization_members`: user, organization, role.
- `channels`: organization, type, display name, credentials JSON, status.
- `customers`: organization, channel, external id, name, username, metadata.
- `conversations`: organization, channel, customer, status, assignment, timestamps.
- `messages`: conversation, direction, sender type, body, external id, raw payload, timestamps.
- `knowledge_base_entries`: organization, title, content, active status.
- `settings`: organization, AI behavior fields and handoff preferences.

Channel credentials are stored in the `channels.credentials` JSON column for the MVP and are only accessed through channel service methods. This keeps the persistence contract narrow so a later vault, KMS, or field-level encryption migration can happen without changing webhook and dashboard code.

## Telegram Flow

1. User creates an organization.
2. User connects a Telegram bot token.
3. Backend validates the token by calling Telegram `getMe`.
4. Backend stores a channel record through the channel service, which is the only module that reads or writes bot credentials.
5. Telegram webhook posts updates to `/api/v1/webhooks/telegram/{channel_id}`.
6. Webhook handler extracts the incoming message, upserts customer, conversation, and inbound message.
7. AI service loads active organization knowledge base entries and builds a concise sales-assistant prompt.
8. Groq generates a reply.
9. Backend stores the AI outbound message.
10. Telegram client sends the reply to the customer.

Webhook processing should be idempotent by external message id where available.

## Instagram Skeleton

Instagram includes production-shaped endpoints but no full OAuth/token exchange flow yet:

- `GET /api/v1/integrations/instagram/oauth/callback`: placeholder for Meta OAuth callback.
- `GET /api/v1/webhooks/instagram`: verifies Meta webhook challenge using `META_VERIFY_TOKEN`.
- `POST /api/v1/webhooks/instagram`: accepts webhook payloads and dispatches to skeleton handlers.
- Meta Graph API client class with methods for future message and comment replies.
- DM and comment handler functions that log accepted events and return structured placeholders.

## Frontend

Pages:

- `/login`
- `/register`
- `/dashboard`
- `/dashboard/onboarding`
- `/dashboard/conversations`
- `/dashboard/customers`
- `/dashboard/knowledge-base`
- `/dashboard/channels`
- `/dashboard/settings`

The dashboard should be usable as an operational SaaS interface. It should avoid marketing-page composition and prioritize dense, scannable workflow screens. Operators can inspect conversations, see customer information, and send manual replies.

## AI Behavior

The AI engine uses Groq chat completions. It receives:

- Organization name.
- Active knowledge base entries.
- Recent conversation messages.
- Incoming customer message.
- Guardrails to answer only from known business information where possible, ask clarifying questions when needed, and keep replies concise.

If `GROQ_API_KEY` is missing, the API should return a clear service configuration error instead of silently faking AI output.

## Error Handling And Logging

Use structured logging via Python logging configuration. API errors should return consistent JSON:

```json
{
  "detail": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE"
}
```

Webhook handlers should log raw integration failures with enough context to diagnose while avoiding secret leakage.

## Deployment

Docker Compose services:

- `api`
- `web`
- `postgres`
- `redis`

Include `.env.example` with all required secrets and ports. The README should explain local setup, migrations, API startup, frontend startup, Telegram webhook configuration, and Instagram placeholder behavior.

## Testing And Verification

Minimum verification:

- Backend import/compile check.
- API test suite for auth, organization creation, knowledge base, and Instagram webhook verification.
- Frontend type check or lint where dependencies permit.
- Docker Compose configuration syntax check if Docker is available.

## Acceptance Criteria

- A developer can run the stack with Docker Compose after copying `.env.example` to `.env`.
- A user can register, login, create an organization, and connect a Telegram bot token.
- Telegram inbound messages are persisted.
- AI replies are generated from Groq using organization knowledge base context.
- AI replies are persisted and sent back through Telegram.
- A human operator can send manual replies from the dashboard.
- Conversations and customers are visible in the admin dashboard.
- Instagram endpoints and client skeletons are present, typed, logged, and ready for future implementation.
- The codebase has a clean, modular structure for adding WhatsApp and website chat later.
