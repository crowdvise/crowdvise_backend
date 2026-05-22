# CrowdVise

Synthetic customer simulation API and marketing site. The backend generates psychologically grounded AI panels (OCEAN + other behavioural and decision making frameworks) that move through a product journey — converting, stalling, or dropping off — so teams can test ideas before shipping.

| Area | Path | Description |
|------|------|-------------|
| **API** | [`backend/`](backend/) | FastAPI service: journey generation, simulation runs, Supabase auth & persistence |
| **Website** | [`website/`](website/) | Static CrowdVise landing page |
| **Database** | [`backend/supabase/schema.sql`](backend/supabase/schema.sql) | `simulation_runs` table + RLS |

## Requirements

- Python 3.11+
- [Anthropic API](https://console.anthropic.com/) key
- [Supabase](https://supabase.com/) project (Auth + Postgres) — optional for local dev with `AUTH_DISABLED=true`

## Quick start (backend)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY
# For local dev without Supabase: AUTH_DISABLED=true

uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- Health: http://127.0.0.1:8000/health  
- Interactive API docs: http://127.0.0.1:8000/docs  

Run commands from the **`backend/`** directory so imports and `.env` resolve correctly.

## API flow

1. **`POST /simulation/generate-stages`** — Plain-English product input → suggested journey stages (editable by the client).
2. **`POST /simulation/run`** — Confirmed stages + panel size (`10`, `25`, or `50`) → full simulation result.
3. **`GET /simulation/history`** / **`GET /simulation/{id}`** — Past runs (requires Supabase auth; skipped when `AUTH_DISABLED=true`).

Protected routes expect:

```
Authorization: Bearer <supabase_access_token>
```

See [`backend/.env.example`](backend/.env.example) for CORS, rate limits, and request size settings.

## Supabase setup

1. Create a project and enable Auth (email, magic link, or OAuth as you prefer).
2. Run [`backend/supabase/schema.sql`](backend/supabase/schema.sql) in the SQL editor.
3. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.

The API inserts runs with the service role and scopes rows by `user_id` from the JWT.

## Website (local preview)

```bash
cd website
python3 -m http.server 8080
```

Open http://localhost:8080. Configure CTA URLs in [`website/js/config.js`](website/js/config.js). More detail: [`website/README.md`](website/README.md).

## Deploy (backend)

[`backend/railpack.json`](backend/railpack.json) targets Python 3.11 with:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set production env vars on the host (never commit `.env`). Use explicit `ALLOWED_ORIGINS` — not `*`.

## Project layout

```
crowdvise/
├── README.md
├── requirements.txt          # -r backend/requirements.txt
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── routers/
│   ├── services/
│   ├── prompts/
│   ├── dependencies/
│   ├── middleware/
│   └── supabase/
└── website/
    ├── index.html
    ├── css/
    └── js/
```

## Security notes

- `.env` files are gitignored; use `.env.example` as the template.
- Do not set `AUTH_DISABLED=true` in production.
- Keep `SUPABASE_SERVICE_ROLE_KEY` server-side only.
