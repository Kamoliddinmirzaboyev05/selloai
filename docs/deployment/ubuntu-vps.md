# Sello AI Ubuntu VPS Deployment Guide

Production domains:

- Frontend: `https://sello.webportfolio.uz`
- Backend API: `https://selloapi.webportfolio.uz`
- Meta OAuth callback URL: `https://selloapi.webportfolio.uz/auth/meta/callback`
- Instagram webhook URL: `https://selloapi.webportfolio.uz/webhooks/instagram`

## 1. DNS

Create `A` records pointing both domains to the VPS public IPv4 address:

```text
sello.webportfolio.uz      A      <VPS_PUBLIC_IP>
selloapi.webportfolio.uz   A      <VPS_PUBLIC_IP>
```

Wait until DNS resolves before requesting SSL certificates.

## 2. Server Packages

```bash
sudo apt update
sudo apt install -y ca-certificates curl git nginx certbot python3-certbot-nginx
```

Install Docker Engine using Docker's official Ubuntu instructions, then verify:

```bash
docker --version
docker compose version
```

## 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Only Nginx should be public. The production Compose file binds the app containers to `127.0.0.1`.

## 4. Application Files

```bash
sudo mkdir -p /opt/sello-ai
sudo chown "$USER":"$USER" /opt/sello-ai
cd /opt/sello-ai
git clone https://github.com/Kamoliddinmirzaboyev05/selloai.git .
```

Create production environment:

```bash
cp .env.production.example .env.production
nano .env.production
```

Required production values:

```text
NEXT_PUBLIC_API_URL=https://selloapi.webportfolio.uz
API_CORS_ORIGINS=https://sello.webportfolio.uz
META_OAUTH_CALLBACK_URL=https://selloapi.webportfolio.uz/auth/meta/callback
INSTAGRAM_WEBHOOK_URL=https://selloapi.webportfolio.uz/webhooks/instagram
API_JWT_SECRET=<long-random-secret>
GROQ_API_KEY=<groq-api-key>
META_VERIFY_TOKEN=<meta-webhook-token>
POSTGRES_PASSWORD=<strong-db-password>
API_DATABASE_URL=postgresql+asyncpg://sello:<strong-db-password>@postgres:5432/sello
```

If the VPS already has projects using ports `3000` or `8000`, set different local-only host ports before starting Compose:

```text
API_HOST_PORT=18000
WEB_HOST_PORT=13000
```

Then update the Nginx upstream ports in `deploy/nginx/sello.conf` on that VPS to match:

```text
Frontend upstream: http://127.0.0.1:13000
Backend upstream:  http://127.0.0.1:18000
```

## 5. Start Production Containers

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Check local container endpoints:

```bash
curl http://127.0.0.1:${API_HOST_PORT:-8000}/api/v1/health
curl -I http://127.0.0.1:${WEB_HOST_PORT:-3000}
```

## 6. Nginx Reverse Proxy

Install the temporary HTTP-only Nginx site first. This lets Nginx start before SSL certificate files exist:

```bash
sudo cp deploy/nginx/sello.http.conf /etc/nginx/sites-available/sello.conf
sudo ln -sf /etc/nginx/sites-available/sello.conf /etc/nginx/sites-enabled/sello.conf
sudo nginx -t
sudo systemctl reload nginx
```

Request separate Let's Encrypt certificates for both production domains:

```bash
sudo certbot certonly --nginx -d sello.webportfolio.uz
sudo certbot certonly --nginx -d selloapi.webportfolio.uz
```

After both certificates exist, install the final HTTPS reverse proxy config:

```bash
sudo cp deploy/nginx/sello.conf /etc/nginx/sites-available/sello.conf
sudo nginx -t
sudo systemctl reload nginx
```

The final config redirects HTTP to HTTPS and proxies:

- `https://sello.webportfolio.uz` -> `127.0.0.1:${WEB_HOST_PORT:-3000}`
- `https://selloapi.webportfolio.uz` -> `127.0.0.1:${API_HOST_PORT:-8000}`
- `https://selloapi.webportfolio.uz/auth/meta/callback` -> `/api/v1/integrations/instagram/oauth/callback`
- `https://selloapi.webportfolio.uz/webhooks/instagram` -> `/api/v1/webhooks/instagram`

Validate Nginx after every config change:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 7. HTTPS/SSL Verification

Verify certificates and HTTPS routing:

```bash
curl -I https://sello.webportfolio.uz
curl https://selloapi.webportfolio.uz/api/v1/health
curl -I "https://selloapi.webportfolio.uz/webhooks/instagram?hub.mode=subscribe&hub.verify_token=<META_VERIFY_TOKEN>&hub.challenge=test"
```

Certbot installs automatic renewal. Test renewal:

```bash
sudo certbot renew --dry-run
```

## 8. Meta App Configuration

In Meta Developers, configure:

- OAuth redirect URI: `https://selloapi.webportfolio.uz/auth/meta/callback`
- Instagram webhook callback URL: `https://selloapi.webportfolio.uz/webhooks/instagram`
- Verify token: the exact value from `META_VERIFY_TOKEN`

The Nginx config maps those clean production URLs to the MVP API routes:

- `/auth/meta/callback` -> `/api/v1/integrations/instagram/oauth/callback`
- `/webhooks/instagram` -> `/api/v1/webhooks/instagram`

## 9. Operations

Deploy updates:

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api
```

Back up PostgreSQL:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > sello-backup.sql
```

Stop the stack:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml down
```
