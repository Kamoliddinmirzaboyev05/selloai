# Sello AI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready MVP SaaS foundation for Sello AI with Telegram fully implemented and Instagram integration skeletons ready for Meta Graph API and Webhooks.

**Architecture:** Use a monorepo with a modular FastAPI backend, a Next.js 15 dashboard frontend, and shared TypeScript DTOs. The backend is a modular monolith with channel adapters feeding common customer, conversation, message, knowledge base, and AI services.

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS, FastAPI, Python 3.12, SQLAlchemy 2.x async, Alembic, PostgreSQL, Redis, JWT, Groq API, Docker Compose.

## Global Constraints

- Use environment variables for all secrets.
- Include `.env.example`.
- Include README with setup steps.
- Include database migrations.
- Include clean folder structure.
- Include error handling and logging.
- Make the code modular and scalable for future WhatsApp and website chat channels.
- Telegram must be fully implemented for the MVP.
- Instagram must include Meta OAuth callback placeholder, webhook verification endpoint, Instagram DM event handler skeleton, Instagram comment event handler skeleton, and Meta Graph API client skeleton.

---

## 1. Project Structure

Create:

```text
apps/
  api/
    alembic/
    app/
      ai/
      auth/
      channels/
      conversations/
      core/
      customers/
      handoff/
      instagram/
      knowledge_base/
      messages/
      organizations/
      settings/
      telegram/
      users/
    tests/
  web/
    app/
    components/
    lib/
packages/
  shared/
docker-compose.yml
.env.example
README.md
```

Root files define the workspace, Docker orchestration, and setup documentation.

## 2. Backend Modules

- `core`: settings, database session, security helpers, error types, logging, app factory.
- `auth`: registration, login, JWT dependency.
- `users`: current user schema and persistence model.
- `organizations`: organization creation, membership, active organization selection.
- `channels`: channel CRUD, credential storage boundary, channel type/status enums.
- `telegram`: token validation, connect bot endpoint, webhook endpoint, update processing, send-message client.
- `instagram`: OAuth callback placeholder, webhook verify endpoint, webhook event dispatcher, Graph API client skeleton.
- `customers`: upsert channel customer records.
- `conversations`: find/create channel conversations, list dashboard conversations.
- `messages`: store inbound/outbound messages, list conversation history.
- `knowledge_base`: CRUD active knowledge entries.
- `ai`: Groq client, prompt builder, response generation.
- `handoff`: manual operator reply endpoint and conversation status update.
- `settings`: organization AI settings and handoff preferences.

## 3. Frontend Pages

- `/login`: email/password login.
- `/register`: account creation.
- `/dashboard`: overview metrics and recent conversations.
- `/dashboard/onboarding`: create first organization.
- `/dashboard/conversations`: inbox list and selected thread.
- `/dashboard/customers`: customer/lead table.
- `/dashboard/knowledge-base`: create and manage knowledge snippets.
- `/dashboard/channels`: connect Telegram and show Instagram placeholder state.
- `/dashboard/settings`: organization settings.

Use a quiet operational dashboard layout with sidebar navigation, tables, forms, and thread views.

## 4. Database Models

Implement SQLAlchemy models and Alembic migration for:

- `users`
- `organizations`
- `organization_members`
- `channels`
- `customers`
- `conversations`
- `messages`
- `knowledge_base_entries`
- `organization_settings`

Enums:

- organization role: `owner`, `admin`, `operator`
- channel type: `telegram`, `instagram`, `whatsapp`, `website_chat`
- channel status: `pending`, `active`, `disabled`, `error`
- conversation status: `open`, `ai_handling`, `human_handoff`, `closed`
- message direction: `inbound`, `outbound`
- sender type: `customer`, `ai`, `operator`, `system`

## 5. API Endpoints

Use `/api/v1` prefix:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /organizations`
- `GET /organizations`
- `GET /organizations/{organization_id}`
- `GET /channels`
- `POST /channels/telegram/connect`
- `GET /conversations`
- `GET /conversations/{conversation_id}/messages`
- `POST /conversations/{conversation_id}/manual-reply`
- `GET /customers`
- `GET /knowledge-base`
- `POST /knowledge-base`
- `PATCH /knowledge-base/{entry_id}`
- `DELETE /knowledge-base/{entry_id}`
- `GET /settings`
- `PATCH /settings`
- `POST /webhooks/telegram/{channel_id}`
- `GET /integrations/instagram/oauth/callback`
- `GET /webhooks/instagram`
- `POST /webhooks/instagram`

## 6. Telegram Integration Flow

1. Authenticated user posts bot token to `/channels/telegram/connect`.
2. API validates token with Telegram `getMe`.
3. API creates or updates a Telegram channel for the organization.
4. Telegram sends messages to `/webhooks/telegram/{channel_id}`.
5. Handler extracts `message.from`, `message.chat.id`, `message.text`, and Telegram message id.
6. API upserts customer and open conversation.
7. API stores inbound message idempotently.
8. AI service loads active knowledge base entries and recent conversation history.
9. Groq returns a reply.
10. API stores outbound AI message.
11. Telegram client sends reply via `sendMessage`.

## 7. Instagram Skeleton Flow

1. Meta redirects to `/integrations/instagram/oauth/callback`; API logs query params and returns a structured placeholder.
2. Meta verifies webhook through `GET /webhooks/instagram` with `hub.mode`, `hub.verify_token`, and `hub.challenge`.
3. API compares `hub.verify_token` to `META_VERIFY_TOKEN`.
4. `POST /webhooks/instagram` accepts webhook JSON.
5. Dispatcher routes messaging events to `handle_instagram_dm_event`.
6. Dispatcher routes comment/change events to `handle_instagram_comment_event`.
7. Graph API client exposes methods for future send-message and reply-comment calls.

## 8. Groq AI Engine Flow

1. AI service receives organization, incoming message, conversation history, and knowledge entries.
2. Prompt builder creates system and user messages.
3. Groq client calls `/openai/v1/chat/completions`.
4. AI service returns concise reply text.
5. If `GROQ_API_KEY` is missing, raise `SERVICE_NOT_CONFIGURED`.
6. If Groq fails, log the response and raise `AI_PROVIDER_ERROR`.

## 9. Docker Setup

Services:

- `postgres`: PostgreSQL 16 with persistent volume.
- `redis`: Redis 7 with persistent volume.
- `api`: Python 3.12 FastAPI app, runs Alembic migrations then Uvicorn.
- `web`: Next.js app served on port 3000.

Environment files:

- Root `.env.example` documents API, web, database, Redis, JWT, Groq, Telegram, and Meta variables.
- Docker Compose reads `.env`.

## 10. First Milestone Tasks

### Task 1: Repository And Runtime Scaffolding

- [ ] Create root workspace files.
- [ ] Create API package, dependency files, Dockerfile, app entrypoint, settings, health route.
- [ ] Create web package, dependency files, Tailwind config, app shell.
- [ ] Create shared package with DTO constants.
- [ ] Verify API imports and frontend TypeScript config load.

### Task 2: Backend Data Layer And Migrations

- [ ] Write SQLAlchemy models and enums.
- [ ] Write Alembic environment and initial migration.
- [ ] Add async session dependency.
- [ ] Add test database fixtures with SQLite-compatible model creation for unit tests.
- [ ] Verify model metadata imports.

### Task 3: Auth, Organizations, And Settings

- [ ] Write tests for register, login, current user, organization creation, and default settings.
- [ ] Implement password hashing, JWT creation, and current-user dependency.
- [ ] Implement organization and membership services.
- [ ] Implement settings service.
- [ ] Verify tests pass.

### Task 4: Core CRM And Knowledge Base

- [ ] Write tests for customer upsert, conversation creation, message persistence, and knowledge base CRUD.
- [ ] Implement customers, conversations, messages, and knowledge base services/routes.
- [ ] Verify tests pass.

### Task 5: Groq AI Engine

- [ ] Write tests for prompt building and missing API key behavior.
- [ ] Implement Groq client and AI response service.
- [ ] Verify tests pass.

### Task 6: Telegram Full MVP Flow

- [ ] Write tests for Telegram update parsing and idempotent inbound persistence.
- [ ] Implement Telegram token validation and connect endpoint.
- [ ] Implement Telegram webhook processing and send-message client.
- [ ] Verify tests pass.

### Task 7: Instagram Skeleton

- [ ] Write tests for webhook verification success/failure and event dispatch.
- [ ] Implement OAuth callback placeholder, webhook endpoints, event handlers, and Graph API client skeleton.
- [ ] Verify tests pass.

### Task 8: Dashboard Frontend

- [ ] Implement auth forms and token storage.
- [ ] Implement dashboard layout and pages.
- [ ] Implement API client and forms for org, channels, knowledge base, conversations, customers, settings, and manual replies.
- [ ] Verify TypeScript build.

### Task 9: Docker, Docs, And Final Verification

- [ ] Add Dockerfiles, Compose, `.env.example`, and README.
- [ ] Run backend tests.
- [ ] Run frontend type check/build.
- [ ] Validate Docker Compose config when Docker is available.
- [ ] Commit implementation.

## Self-Review

- Spec coverage: every approved scope item maps to Tasks 1-9.
- Placeholder scan: Instagram has intentional skeleton endpoints; implementation tasks require structured placeholders rather than missing code.
- Type consistency: backend entity names, endpoint names, and enum values match the design spec.
