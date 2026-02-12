# HarnessAI - The Mirror: Build Notes

## Overview

"The Mirror" is an operational intelligence platform that analyzes businesses using public data and generates structured profiles via Claude Sonnet. Built as a proof-of-competence engine for HarnessAI.

**Built:** February 2026
**Stack:** FastAPI (Python) + Next.js (React) + Postgres + Redis
**Deployment:** Docker Compose via Coolify

---

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│    Frontend     │     │              Orchestrator                │
│   (Next.js)     │────▶│              (FastAPI)                   │
│   Port 3000     │     │              Port 8000                   │
└─────────────────┘     └──────────────────────────────────────────┘
                                         │
                        ┌────────────────┼────────────────┐
                        ▼                ▼                ▼
                  ┌──────────┐    ┌──────────┐    ┌──────────┐
                  │ Postgres │    │  Redis   │    │ External │
                  │  :5432   │    │  :6379   │    │   APIs   │
                  └──────────┘    └──────────┘    └──────────┘
```

### Four Docker Services

| Service | Image | Purpose |
|---------|-------|---------|
| `frontend` | Next.js 16 | Intake form + Profile view |
| `orchestrator` | Python 3.12 | API + Workers + Profile generation |
| `postgres` | postgres:16-alpine | Persistent storage |
| `redis` | redis:7-alpine | Rate limiting + Caching |

---

## User Flow

1. Visitor submits company name, URL, and business email
2. System validates email domain matches URL domain
3. Parallel data collection runs (5 workers, 10s timeout each)
4. Aggregated data sent to Claude Sonnet for analysis
5. Profile stored in Postgres
6. Email sent with private, expiring link (7 days)
7. Visitor views profile with staged animation

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check for Coolify |
| `POST` | `/intake` | Submit company for analysis |
| `GET` | `/status/{job_id}` | Check job status |
| `GET` | `/profile/{token}` | Get profile (auth via URL token) |
| `POST` | `/profile/{token}/feedback` | Submit rating (1-5) |

### POST /intake Request
```json
{
  "company_name": "Acme Inc",
  "company_url": "acme.com",
  "email": "user@acme.com"
}
```

### Profile Response Structure
```json
{
  "company_name": "string",
  "industry_classification": "string",
  "location": "string",
  "estimated_size": "string",
  "operational_snapshot": {
    "technology_posture": "string",
    "digital_maturity": "string (1-10 rating)",
    "detected_technologies": ["array"],
    "infrastructure_signals": "string"
  },
  "market_position": {
    "business_category": "string",
    "public_reputation": "string",
    "competitive_signals": "string",
    "growth_indicators": "string"
  },
  "strategic_observations": ["array of insights"],
  "identified_gaps": ["array of opportunities"],
  "data_confidence": {
    "overall_score": "High/Medium/Low",
    "sources_used": ["array"],
    "sources_unavailable": ["array"],
    "freshness": "string"
  }
}
```

---

## Data Collection Workers

All workers run in parallel with 10-second timeout. If a worker fails, system proceeds with available data.

| Worker | File | Data Source | Extracts |
|--------|------|-------------|----------|
| Site Scraper | `site_scraper.py` | Target URL | Title, meta, text, navigation, internal links, about/services/team pages |
| Tech Detector | `tech_detector.py` | HTTP headers + HTML | CMS, frameworks, analytics, CDN, payment processors (50+ signatures) |
| DNS/WHOIS | `dns_whois.py` | DNS + WHOIS | MX records, email provider, SPF/DKIM/DMARC, nameservers, domain age |
| Google Business | `google_business.py` | Google Places API | Rating, reviews, category, hours, phone, address |
| Job Scanner | `job_scanner.py` | SerpAPI | Open positions, job titles, departments, seniority levels |

### Technology Signatures (tech_detector.py)

Detects 50+ technologies including:
- **CMS:** WordPress, Shopify, Squarespace, Wix, Webflow, Drupal, HubSpot
- **Frameworks:** React, Vue.js, Angular, Next.js, Gatsby
- **Analytics:** GA4, Mixpanel, Segment, Hotjar, Facebook Pixel
- **CDN:** Cloudflare, AWS CloudFront, Fastly, Akamai
- **Hosting:** Vercel, Netlify, Heroku, AWS, Google Cloud
- **E-commerce:** WooCommerce, Magento, BigCommerce
- **Marketing:** Mailchimp, HubSpot, Salesforce, Intercom, Zendesk

---

## Database Schema

### submissions
```sql
id SERIAL PRIMARY KEY
company_name VARCHAR(255)
company_url VARCHAR(500)
email VARCHAR(255)
job_id UUID UNIQUE
auth_token UUID UNIQUE
status VARCHAR(50)  -- queued/processing/complete/failed/manual_review/insufficient_data
created_at TIMESTAMP
completed_at TIMESTAMP
```

### profiles
```sql
id SERIAL PRIMARY KEY
submission_id INTEGER REFERENCES submissions(id)
profile_json JSONB
data_sources_used TEXT[]
confidence_score VARCHAR(50)
created_at TIMESTAMP
```

### feedback
```sql
id SERIAL PRIMARY KEY
profile_id INTEGER REFERENCES profiles(id)
rating INTEGER CHECK (1-5)
comment TEXT
created_at TIMESTAMP
```

---

## Frontend Pages

### Intake Page (`/`)
- Three fields: Company Name, Company URL, Business Email
- Single submit button
- Success message after submission

### Profile Page (`/profile/[token]`)
- Authenticated via URL token
- Staged panel animation (300ms stagger)
- Asymmetric grid: 65% left (primary data), 35% right (confidence, CTA)
- CTA appears only after animation completes

### Design System
- **Font:** Inter (400, 500, 600)
- **Sizes:** 14px body, 12px meta, 18px headers, 28px company name
- **Color:** #1a2b4a (deep ink blue) - interactive elements only
- **Animation:** translateY(20px→0) + opacity(0→1) over 200ms ease-out

---

## Quality Gates

1. **Email Domain Validation**
   - Must match URL domain (flexible: company.com accepts mail.company.com)
   - Gmail/Yahoo/Outlook flagged for manual review (not rejected)

2. **Data Sufficiency Check**
   - Minimum 3 "points" of data required
   - Site scraper = 2 points, others = 1 point each
   - If insufficient: status = "insufficient_data", different email sent

3. **Profile Validation**
   - Checks detected_technologies against worker output
   - Flags fabricated data (doesn't fail, adds _validation_issues)

4. **Rate Limiting**
   - 10 submissions per IP per hour (via Redis)

5. **Token Expiration**
   - Profile links expire after 7 days

---

## Anthropic Integration

- **Model:** claude-sonnet-4-5-20250929
- **Max tokens:** 2500
- **Temperature:** 0.3 (consistency over creativity)
- **Retry:** 3 attempts with exponential backoff (1s, 4s, 16s)

---

## File Structure

```
h2/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── SETUP.md              # Deployment guide
├── BUILD_NOTES.md        # This file
├── h2.md                 # Original spec
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   └── app/
│       ├── globals.css       # Design system
│       ├── layout.tsx        # Root layout
│       ├── page.tsx          # Intake form
│       └── profile/[token]/
│           └── page.tsx      # Profile view
│
└── orchestrator/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── __init__.py
        ├── main.py           # FastAPI app + endpoints
        ├── config.py         # Environment settings
        ├── database.py       # Postgres operations
        ├── schemas.py        # Pydantic models
        ├── workers/
        │   ├── __init__.py
        │   ├── site_scraper.py
        │   ├── tech_detector.py
        │   ├── dns_whois.py
        │   ├── google_business.py
        │   └── job_scanner.py
        └── services/
            ├── __init__.py
            ├── anthropic_service.py
            └── email_service.py
```

---

## Dependencies

### Orchestrator (Python)
```
fastapi
uvicorn[standard]
httpx
beautifulsoup4
lxml
python-whois
dnspython
anthropic
psycopg[binary]
redis
resend
pydantic
pydantic-settings
```

### Frontend (Node.js)
```
next@16.1.6
react@19.2.4
react-dom@19.2.4
typescript@5.9.3
```

---

## What's NOT Built (Phase 2)

Per spec, these are explicitly excluded from MVP:
- User accounts / login system
- Admin dashboard
- PDF export
- Competitor comparison view
- Strategic question decomposition
- Payment processing

---

## External Services Required

| Service | Purpose | Cost |
|---------|---------|------|
| Anthropic | Profile generation | Pay per token |
| Resend | Transactional email | Free tier: 3k/month |
| Google Places | Business data | $17/1k requests |
| SerpAPI | Job postings | Optional, $50/month |

---

## Deployment Checklist

- [ ] Push to GitHub
- [ ] Create Coolify Docker Compose resource
- [ ] Set environment variables in Coolify
- [ ] Configure DNS (A records for app + api subdomains)
- [ ] Assign domains in Coolify
- [ ] Deploy
- [ ] Verify health endpoint
- [ ] Test intake submission
- [ ] Verify email delivery (check Resend logs)
- [ ] Test profile view

---

## Git Repository

**URL:** https://github.com/carywoods/h2

**Commits:**
1. Initial commit - Full MVP implementation
2. Add Coolify quick start variables to SETUP.md
3. Update dependencies to fix security vulnerabilities
