# VeinConnect AI 🩸

**AI-Powered Recurring Transfusion Coordination Platform for Thalassemia Care**

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 16+

### 1. Clone & Setup

```bash
git clone <repo-url>
cd Vein_connect_ai
cp backend/.env.example backend/.env
# Edit backend/.env with your secrets
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

API available at: http://localhost:8000  
API Docs: http://localhost:8000/docs  
Health Check: http://localhost:8000/health

### 3. Local Development (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

## Architecture

```
frontend/          # Next.js 15 + TypeScript + Tailwind + ShadCN
backend/
  app/
    api/v1/       # FastAPI route handlers (14 modules)
    services/     # Business logic layer (14 services)
    repositories/ # Data access layer (15 repositories)
    models/       # SQLAlchemy ORM models (20 models)
    schemas/      # Pydantic request/response schemas (14 modules)
    ai/           # AI engines (8 engines)
    core/         # Security, exceptions, permissions
    middleware/   # Rate limiting, audit logging, error handling
  alembic/        # Database migrations
```

## API Reference

All endpoints are prefixed with `/api/v1/`.

| Module | Base Path | Description |
|--------|-----------|-------------|
| Auth | `/auth` | JWT signup, login, refresh |
| Patients | `/patients` | Patient registration & profiles |
| Donors | `/donors` | Donor registration, availability |
| Coordinators | `/coordinators` | Coordinator workflow |
| Hospitals | `/hospitals` | Hospital capacity management |
| Transfusions | `/transfusions` | Full transfusion lifecycle |
| Confirmations | `/confirmations` | 4-party consensus |
| Notifications | `/notifications` | In-app notification inbox |
| Rewards | `/rewards` | Points, tiers, leaderboard |
| Wallets | `/wallets` | Balance & transactions |
| Expenses | `/expenses` | Donor reimbursements |
| Emergency | `/emergency` | Emergency escalation |
| Incidents | `/incidents` | System incident tracking |
| Admin | `/admin` | Platform management |

## AI Engines

| Engine | Algorithm | Purpose |
|--------|-----------|--------|
| Donor Matcher | Weighted scoring (6 factors) | Rank donors for transfusion |
| Reliability | EWMA | Donor reliability score |
| Response Likelihood | Rule-based | Probability of donor response |
| Transfusion Predictor | Recency-weighted MA | Next transfusion date |
| Emergency Prioritizer | Distance-first scoring | Emergency donor ranking |
| Capacity Forecaster | Rolling weekday average | Hospital capacity prediction |
| Communication | Template engine | Bilingual message selection |
| Friendship Score | Multi-factor formula | Patient-donor relationship |

## Key Design Principles

1. **AI recommends, humans decide** — AI never directly schedules transfusions
2. **4-party consensus** — All transfusions require Patient + Donor + Coordinator + Hospital confirmation
3. **Soft deletes** — No data is physically deleted (audit trail preserved)
4. **Role-based access** — 5 roles: patient, donor, coordinator, hospital, admin
5. **Emergency escalation** — Bypasses normal flow, all donors alerted simultaneously

## License

MIT License — Built for healthcare hackathon purposes.
