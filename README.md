# Recall API (FastAPI + SQLAlchemy)

Backend for the uploaded wireframes: **Recall** (auth, dashboard, spaced-repetition review) and
**ProcureMind / mem0** (memory stream, knowledge intelligence, team profiles, vendors, PO checkout).

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set JWT_SECRET and VENDOR_SECRET_KEY
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --reload   # docs: http://localhost:8000/docs
pytest -q                       # tests/test_api.py is an end-to-end smoke test
```
SQLite by default; set `DATABASE_URL=postgresql+psycopg://...` for Postgres (add `psycopg[binary]`).
Tables are auto-created on startup; use Alembic before going to production.

All routes are under `/api/v1`. Send `Authorization: Bearer <token>`, or `X-API-Key` for agents.

## Query Mind (Hindsight)
Frontend (`frontend/chat.html`) -> `POST /api/v1/assistant/ask` -> Hindsight **recall** -> **reflect** (answer) -> answer + sources.
- The Hindsight API key and bank id live only in backend `.env` (`HINDSIGHT_API_KEY`, `HINDSIGHT_BANK_ID=vision-mind`). The browser never sees them; `/assistant/status` returns only booleans.
- Endpoints: `GET /assistant/status?check=true`, `POST /assistant/ask {question}`, `POST /assistant/retain {content, context}` (save new knowledge).
- No memories found -> "not available" (no LLM call), so nothing is invented. Reflect failure -> falls back to the recalled snippets.
- If your bank is spelled differently in Hindsight Cloud, change `HINDSIGHT_BANK_ID` in `.env` and restart.

## Database
15 tables (see `database/schema.template.sql`; the ORM in `app/models.py` is the source of truth and both match).
```bash
# SQLite (default, zero setup): recall.db is included and already seeded. To rebuild:
python database/init_sqlite.py --reset            # add --no-seed for an empty schema
# PostgreSQL:
docker compose up -d                              # applies database/schema.postgres.sql on first start
export DATABASE_URL=postgresql+psycopg://recall:recall@localhost:5432/recall
pip install "psycopg[binary]" && uvicorn app.main:app --reload && python seed_demo.py
```
Edit `schema.template.sql`, then `python database/build_schema.py` to regenerate both dialect files.
Demo login: `alex@company.com` / `RecallMemoryPass2025` (use `init_sqlite.py` **or** `seed_demo.py`, not both, or cards duplicate).
Not yet done: Alembic migrations. Add them before changing the schema in production.

## Prototype UI (frontend ↔ backend connection)
```bash
python seed_demo.py          # optional: creates alex@company.com / RecallMemoryPass2025 + 3 cards (server must be running)
# open http://localhost:8000/   (FastAPI serves ./frontend, same origin, no CORS needed)
```
`frontend/recall-connect.js` is the only glue: login/signup → dashboard (live queue, retention, quick capture) → review
(real SM-2 cards, Again/Hard/Good/Easy) → memory stream (search, verify/pin, edit, delete, add). Token is kept in
localStorage ("remember me") or sessionStorage. Social/passkey buttons show the backend's 501 message.
To use other Stitch exports, add them to `PAGES` in `build_frontend.py` and re-run it.

## Screen → endpoint map
| Screen | Endpoints |
|---|---|
| Sign up / Log in / Forgot | `POST /auth/signup`, `/auth/login` (email or handle, `remember_me`), `/auth/forgot-password`, `/auth/reset-password`, `GET /auth/me` |
| Google / Apple / GitHub / Face ID / Passkey | `POST /auth/oauth/{provider}` → 501 stub (see below) |
| Dashboard | `GET /dashboard`, `GET /stats`, `GET /decks`, `POST /memories` (quick capture: text, #tags, URLs) |
| Review session | `POST /review/sessions`, `POST /review/sessions/{id}/answer` (again/hard/good/easy), `/finish`, `GET /review/queue` |
| Memory stream | `GET /memories?q=&tag=&status=&sort=decay`, `GET /memories/search?q=` (agent recall), `PATCH/DELETE /memories/{id}` |
| Knowledge intelligence | `GET /intelligence/overview`, `/clusters`, `/tuneup`, `/contradictions` (+`/detect`, `/{id}/resolve`, `/{id}/dismiss`), `/duplicates` (+`/merge`) |
| Profiles / team | `GET /workspace`, `PATCH /workspace/settings`, `/workspace/members`, `/invitations`, `/transfer-ownership`, `/leave`, `/audit-log`, `/api-keys` |
| Vendors & integrations | `GET /vendors/catalog`, `/connections`, `/overview`; `POST /vendors/connections`, `/vendors/test`, `/connections/{id}/test`, `/rotate-key`, `/usage` |
| PO checkout / confirmation | `POST /procurement/quote`, `/orders`, `GET /orders/{id}` (live provisioning steps), `/approve`, `/reject`, `/invoice`, `/cost-centers` |

## Design notes
- **SRS**: SM-2 variant in `services/srs.py` (Again 10m → Hard/Good/Easy). Retention = `0.9^(elapsed/interval)`.
- **Roles**: owner, admin, member, read_only, auditor. Auditors never see raw memories. Non-admins only see their own memories or their assigned partitions. `isolate_personal_work` hides `personal` memories from everyone but the owner of each memory.
- **Vendor secrets** are Fernet-encrypted at rest and never returned by the API.
- **Purchase orders**: quote → order → auto-approved if total ≤ `AUTO_APPROVE_LIMIT` and within cost-center budget, else `pending_approval` (admins approve, never their own). Fulfilment is simulated by timer when `PROVISIONING_SIMULATION=true`; set it to `false` and call `POST /orders/{id}/provisioning-events` from your real vendor webhook. Completing an order creates the vendor connection automatically.

## What is stubbed or needs your input
- **Social login, Face ID, passkeys**: need provider client IDs / WebAuthn; the route exists but returns 501.
- **Emails** (password reset, invitations): tokens are printed to the console; add a sender where marked `TODO`.
- **Search / contradiction / dedupe** use lightweight text similarity. Swap in embeddings + a vector store (the Vendors module is where those get connected).
- **Vendor "Authenticate & Test"** checks reachability and latency only, not credentials.
- **Prices/plans** in `services/catalog.py` are placeholders from the wireframe. The wireframe total ($1,459.65) implies ~8.002% tax; the code uses a flat 8% (`TAX_RATE`), giving $1,459.62.
- **Card/billing**: only a payment-method *label* is stored; never send card numbers. Integrate Stripe for real payments.
- The frontend's static demo data (e.g. "Alex Vance") is not seeded.
