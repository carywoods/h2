# HarnessAI - The Mirror Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Local Development](#local-development)
4. [Production Deployment with Coolify](#production-deployment-with-coolify)
5. [Using External Services](#using-external-services)
6. [Domain Configuration](#domain-configuration)
7. [Verification](#verification)

---

## Prerequisites

### Required API Keys
- **Anthropic API Key** - For Claude Sonnet profile generation
  - Get at: https://console.anthropic.com/
- **Resend API Key** - For transactional emails
  - Get at: https://resend.com/
  - Verify your sending domain in Resend dashboard

### Optional API Keys
- **Google Places API Key** - For business profile data
  - Get at: https://console.cloud.google.com/
  - Enable "Places API" and "Places API (New)"
- **SerpAPI Key** - For job posting searches
  - Get at: https://serpapi.com/

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key | `sk-ant-api03-...` |
| `RESEND_API_KEY` | Yes | Resend API key | `re_123abc...` |
| `DB_PASSWORD` | Yes | Postgres password | `strongpassword123` |
| `DATABASE_URL` | No* | Full Postgres connection string | See below |
| `REDIS_URL` | No* | Full Redis connection string | See below |
| `BASE_URL` | Yes | Frontend URL (for email links) | `https://app.harnessai.co` |
| `NEXT_PUBLIC_API_URL` | Yes | API URL (for browser requests) | `https://api.harnessai.co` |
| `GOOGLE_PLACES_API_KEY` | No | Google Places API key | `AIza...` |
| `SERPAPI_KEY` | No | SerpAPI key | `abc123...` |

*If using the bundled Postgres/Redis containers, these are set automatically in docker-compose.yml

---

## Local Development

### Option A: Full Docker Stack (Recommended)

1. **Clone and configure**
   ```bash
   cd h2
   cp .env.example .env
   ```

2. **Edit `.env`**
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   RESEND_API_KEY=re_your-key-here
   DB_PASSWORD=localdev123
   BASE_URL=http://localhost:3000
   NEXT_PUBLIC_API_URL=http://localhost:8000
   GOOGLE_PLACES_API_KEY=your-key-here
   SERPAPI_KEY=your-key-here
   ```

3. **Start the stack**
   ```bash
   docker compose up --build
   ```

4. **Access**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option B: Local Python + External Services

1. **Start only Postgres and Redis**
   ```bash
   docker compose up postgres redis -d
   ```

2. **Run orchestrator locally**
   ```bash
   cd orchestrator
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   export DATABASE_URL=postgresql://harness:localdev123@localhost:5432/harnessai
   export REDIS_URL=redis://localhost:6379
   export ANTHROPIC_API_KEY=your-key
   export RESEND_API_KEY=your-key
   export BASE_URL=http://localhost:3000

   uvicorn app.main:app --reload --port 8000
   ```

3. **Run frontend locally**
   ```bash
   cd frontend
   npm install
   NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
   ```

---

## Production Deployment with Coolify

### Step 1: Prepare Your Server

Ensure Coolify is installed on your server. See https://coolify.io/docs/installation

### Step 2: Create the Application

1. In Coolify dashboard, click **"+ Add Resource"**
2. Select **"Docker Compose"**
3. Connect your GitHub repo containing this project
4. Set the **branch** (e.g., `main`)

### Step 3: Configure Environment Variables

In Coolify, go to **Environment Variables** and add:

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-production-key
RESEND_API_KEY=re_your-production-key
DB_PASSWORD=use-a-strong-random-password
BASE_URL=https://app.harnessai.co
NEXT_PUBLIC_API_URL=https://api.harnessai.co
GOOGLE_PLACES_API_KEY=your-key
SERPAPI_KEY=your-key
```

### Step 4: Configure Domains

See [Domain Configuration](#domain-configuration) below.

### Step 5: Deploy

Click **Deploy**. Coolify will:
- Build the Docker images
- Start all containers
- Configure internal networking
- Provision SSL certificates

---

## Using External Services

### External Postgres Database

If using a managed Postgres service (Supabase, Neon, AWS RDS, DigitalOcean, etc.):

1. **Modify `docker-compose.yml`** - Remove or comment out the postgres service:
   ```yaml
   services:
     # postgres:
     #   image: postgres:16-alpine
     #   ... (comment out entire service)
   ```

2. **Update orchestrator environment** in docker-compose.yml:
   ```yaml
   orchestrator:
     environment:
       - DATABASE_URL=postgresql://username:password@your-db-host.com:5432/harnessai
   ```

3. **Example connection strings:**

   **Supabase:**
   ```
   DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

   **Neon:**
   ```
   DATABASE_URL=postgresql://[user]:[password]@[endpoint].neon.tech/harnessai?sslmode=require
   ```

   **AWS RDS:**
   ```
   DATABASE_URL=postgresql://harness:[password]@mydb.abc123.us-east-1.rds.amazonaws.com:5432/harnessai
   ```

   **DigitalOcean Managed Database:**
   ```
   DATABASE_URL=postgresql://harness:[password]@db-postgresql-nyc1-12345-do-user-123456-0.b.db.ondigitalocean.com:25060/harnessai?sslmode=require
   ```

4. **Initialize the database** - The app auto-creates tables on startup, but you can also run manually:
   ```sql
   -- Connect to your external database and the tables will be created
   -- automatically when the orchestrator starts
   ```

### External Redis

If using managed Redis (Upstash, Redis Cloud, AWS ElastiCache, etc.):

1. **Modify `docker-compose.yml`** - Remove or comment out the redis service

2. **Update orchestrator environment:**
   ```yaml
   orchestrator:
     environment:
       - REDIS_URL=redis://default:[password]@your-redis-host.com:6379
   ```

3. **Example connection strings:**

   **Upstash:**
   ```
   REDIS_URL=rediss://default:[password]@usw1-abc123.upstash.io:6379
   ```
   Note: `rediss://` (with double s) for TLS

   **Redis Cloud:**
   ```
   REDIS_URL=redis://default:[password]@redis-12345.c1.us-east-1-2.ec2.cloud.redislabs.com:12345
   ```

   **AWS ElastiCache:**
   ```
   REDIS_URL=redis://your-cluster.abc123.0001.use1.cache.amazonaws.com:6379
   ```

### Full External Services Example

Here's a complete `docker-compose.yml` using only external Postgres and Redis:

```yaml
services:
  frontend:
    build:
      context: ./frontend
      args:
        - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    depends_on:
      - orchestrator
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 5s
      retries: 3

  orchestrator:
    build: ./orchestrator
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
      - RESEND_API_KEY=${RESEND_API_KEY}
      - SERPAPI_KEY=${SERPAPI_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - BASE_URL=${BASE_URL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

# No volumes needed when using external services
```

And the corresponding `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxx
RESEND_API_KEY=re_xxx
BASE_URL=https://app.harnessai.co
NEXT_PUBLIC_API_URL=https://api.harnessai.co
GOOGLE_PLACES_API_KEY=AIza...
SERPAPI_KEY=xxx

# External Postgres (Supabase example)
DATABASE_URL=postgresql://postgres.xxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# External Redis (Upstash example)
REDIS_URL=rediss://default:xxx@usw1-xxx.upstash.io:6379
```

---

## Domain Configuration

### Two-Domain Setup (Recommended)

| Service | Domain | Set In Coolify |
|---------|--------|----------------|
| frontend | `app.harnessai.co` | Frontend service → Domains |
| orchestrator | `api.harnessai.co` | Orchestrator service → Domains |

**DNS Configuration (at your registrar):**
```
Type  Name   Value
A     app    YOUR_SERVER_IP
A     api    YOUR_SERVER_IP
```

**Environment Variables:**
```env
BASE_URL=https://app.harnessai.co
NEXT_PUBLIC_API_URL=https://api.harnessai.co
```

### Coolify Domain Assignment

1. Go to your deployed resource in Coolify
2. Click on the **frontend** service
3. Go to **"Network"** or **"Domains"** tab
4. Add domain: `app.harnessai.co`
5. Enable **"Generate SSL"** (uses Let's Encrypt)
6. Repeat for **orchestrator** service with `api.harnessai.co`

### Single Domain with Subpath (Alternative)

If you want everything on one domain:

| Path | Service |
|------|---------|
| `harnessai.co/*` | frontend |
| `harnessai.co/api/*` | orchestrator |

This requires Traefik path-based routing configuration in Coolify, which is more advanced.

---

## Verification

### 1. Health Check
```bash
curl https://api.harnessai.co/health
# Expected: {"status":"ok"}
```

### 2. Test Intake Submission
```bash
curl -X POST https://api.harnessai.co/intake \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "company_url": "example.com",
    "email": "test@example.com"
  }'
# Expected: {"job_id":"uuid-here","message":"..."}
```

### 3. Check Frontend
- Visit https://app.harnessai.co
- You should see the intake form

### 4. Check Database Connection
```bash
# If you have psql access to your database:
psql $DATABASE_URL -c "SELECT COUNT(*) FROM submissions;"
```

### 5. Check Redis Connection
```bash
# The orchestrator logs will show Redis connection status on startup
docker compose logs orchestrator | grep -i redis
```

---

## Troubleshooting

### "Connection refused" to API from browser
- Ensure `NEXT_PUBLIC_API_URL` points to the external API domain, not `orchestrator:8000`
- Verify the API domain has SSL configured

### Database connection errors
- Check `DATABASE_URL` format matches your provider's requirements
- Ensure `?sslmode=require` is added for cloud databases
- Verify IP allowlist includes your server

### Emails not sending
- Verify domain is configured in Resend dashboard
- Check the "from" address matches your verified domain
- Review orchestrator logs for Resend errors

### Profile generation fails
- Check Anthropic API key is valid
- Review orchestrator logs for specific errors
- Ensure at least the site scraper can reach the target URL

---

## Quick Reference

### Minimum Required Services
- Orchestrator (FastAPI)
- Frontend (Next.js)
- Postgres (bundled or external)
- Redis (bundled or external)

### Minimum Required Environment Variables
```env
ANTHROPIC_API_KEY=xxx
RESEND_API_KEY=xxx
DB_PASSWORD=xxx          # or DATABASE_URL for external
BASE_URL=https://...
NEXT_PUBLIC_API_URL=https://...
```

### Ports
| Service | Internal | External |
|---------|----------|----------|
| Frontend | 3000 | 443 (via Coolify proxy) |
| Orchestrator | 8000 | 443 (via Coolify proxy) |
| Postgres | 5432 | Not exposed |
| Redis | 6379 | Not exposed |
