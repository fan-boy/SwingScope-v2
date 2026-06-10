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

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Backend | FastAPI, Pydantic |
| Database | Postgres via Supabase |
| Auth | Supabase Auth |
| Package manager | pnpm (monorepo) |
