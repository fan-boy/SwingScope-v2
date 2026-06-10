# SwingScope v2

Private swing-trading dashboard. Monorepo with Next.js frontend and FastAPI backend.

## Structure

```
swingscope/
├── apps/
│   ├── web/          # Next.js 15 frontend
│   └── api/          # FastAPI backend
└── packages/
    ├── ui/           # Shared UI (future)
    └── types/        # Shared types (future)
```

## Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.11+
- Supabase project

## Setup

### 1. Install dependencies

```bash
pnpm install          # installs frontend deps
```

### 2. Frontend env

```bash
cp apps/web/.env.example apps/web/.env.local
# fill in NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### 3. Backend env

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
```

### 4. Run

```bash
# Terminal 1 — frontend
pnpm dev:web

# Terminal 2 — backend
pnpm dev:api
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Pages

| Route | Description |
|-------|-------------|
| `/login` | Auth |
| `/dashboard` | Trade ideas |
| `/watchlist` | Tracked tickers |
| `/settings` | User preferences |

## Database ERD

```
users
 ├─── watchlists ──── watchlist_items
 ├─── trade_plans ─── trade_orders ─── positions
 └─── app_settings

scan_runs ──── scan_candidates ──── trade_plans
                                         │
                                    trade_orders
                                         │
                                      positions

execution_logs  (append-only, references any entity by entity_type + entity_id)
```

### Key relationships
| Table | Relates to | Via |
|-------|-----------|-----|
| `watchlists` | `users` | `user_id` |
| `watchlist_items` | `watchlists` | `watchlist_id` |
| `scan_candidates` | `scan_runs` | `scan_run_id` |
| `trade_plans` | `users` + `scan_candidates` | `user_id`, `candidate_id` |
| `trade_orders` | `trade_plans` + `positions` | `plan_id`, `position_id` |
| `app_settings` | `users` | `user_id` (1-to-1) |
| `execution_logs` | any | `entity_type` + `entity_id` (polymorphic) |

### Query optimisations
- `scan_candidates` indexed on `(symbol, run_date)` — fast latest-score lookup
- `scan_candidates` indexed on `score DESC` — fast top-N queries
- `trade_orders` indexed on `status` — fast pending/filled filter
- `execution_logs` indexed on `created_at` — fast recent-events query
- `positions` indexed on `(symbol, status)` — fast open-position lookup

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Backend | FastAPI, Pydantic |
| Database | Postgres via Supabase |
| Auth | Supabase Auth |
| Package manager | pnpm (monorepo) |
