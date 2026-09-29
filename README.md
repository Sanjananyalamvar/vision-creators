# Query Mind

Internal AI assistant that answers employee questions from company documents stored in **Hindsight** (bank `vision-mind`).

```
Browser (frontend/)  →  FastAPI backend (backend/)  →  Hindsight Cloud
                                                     ↳ Recall  (find relevant company memories → shown as sources)
                                                     ↳ Reflect (write the answer from those memories, following Query Mind's rules)
                        ← answer + sources ←
                                                     ↳ Retain  ("Helpful – remember this" button saves a good Q&A)
```

The Hindsight API key lives **only** in `backend/.env`. The frontend calls `/api/*` on your own server and never receives the key
(`/api/health` reports just `hindsight_configured: true/false`).

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** (the backend also serves the frontend, so there is no CORS setup).
Interactive API docs: http://localhost:8000/docs

Run the tests (no network or key needed, Hindsight is faked): `pytest -q`

## Configuration (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `HINDSIGHT_API_KEY` | – | Your Hindsight Cloud key (server only) |
| `HINDSIGHT_BASE_URL` | `https://api.hindsight.vectorize.io` | Hindsight Cloud endpoint |
| `HINDSIGHT_BANK_ID` | `vision-mind` | Memory bank that holds the company documents |
| `HINDSIGHT_BUDGET` | `mid` | Search effort: `low`, `mid`, `high` |
| `RATE_LIMIT_PER_MINUTE` | `20` | Per-IP limit so a public demo can't burn your quota |

If your bank in the Hindsight dashboard is spelled differently from `vision-mind`, change `HINDSIGHT_BANK_ID`.

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/chat` `{question}` | Recall + Reflect → `{answer, sources[], mode}` |
| `POST /api/retain` `{question, answer}` | Save a helpful Q&A to memory |
| `GET /api/examples` | The five sample questions |
| `GET /api/health` | Status, and whether the key is configured |

Behaviour: if Reflect fails but Recall works, the user still gets the retrieved notes (`mode: "recall_only"`). If Hindsight has nothing relevant, the
answer says the information isn't available. Upstream error details are logged server-side (with the key scrubbed) and never sent to the browser.

## Files

- `backend/app/hindsight_service.py`: the only place that talks to Hindsight
- `backend/app/prompts.py`: the Query Mind instructions passed to Reflect, plus the example questions
- `backend/app/main.py`: routes, fallbacks, rate limiting, static hosting of `frontend/`
- `frontend/`: `index.html`, `styles.css`, `app.js` (plain HTML/CSS/JS, no build step)
