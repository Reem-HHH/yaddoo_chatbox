# Yaddoo (مجلس يَدّوه)

Arabic/Emirati grandma chatbot for kids. A Flask backend proxies chat requests to
the Groq API; a static frontend provides the RTL chat UI.

- `backend/app.py` — Flask API (`/api/chat`, `/health`, `/`). Defaults to port `3000`.
- `frontend/` — static `index.html`, `app.js`, `styles.css`, and `assets/`.

## Cursor Cloud specific instructions

Services (run each in its own terminal; leave both running for local dev):

| Service  | Command | Port | Notes |
| -------- | ------- | ---- | ----- |
| Backend  | `set -a; . /workspace/.env; set +a; cd backend && /workspace/.venv/bin/python app.py` | 3000 | Flask dev server (`debug=True`). |
| Frontend | `cd frontend && /workspace/.venv/bin/python -m http.server 5500` | 5500 | Any static server works. |

Open the app at `http://localhost:5500/index.html`. There is no build step and no
lint/test suite in this repo.

Non-obvious caveats:
- Env loading: `app.py` calls `load_dotenv(BASE_DIR / ".env")`, i.e. it looks for
  `backend/.env` (which does not exist). The committed key lives in the repo-root
  `/workspace/.env`, so export it into the shell before launching (the backend
  command above does this via `set -a; . /workspace/.env`), or copy it to
  `backend/.env`. `GET /health` returns `"has_key": true` once the key is loaded.
- The frontend hardcodes its API base: on `localhost`/`127.0.0.1` it calls
  `http://localhost:3000`, otherwise the public Render URL. Keep the backend on
  port 3000 for local testing.
- Rule-based replies (greetings, small talk, very short/garbled input) are answered
  locally without calling Groq — useful for smoke-testing without a valid key.
- LLM replies require a VALID `GROQ_API_KEY`. The key committed in `.env` currently
  returns `401 Invalid API Key` from Groq, so full LLM answers need a working key
  supplied via the `GROQ_API_KEY` secret/env var. Also note `mixtral-8x7b-32768`
  in `GROQ_MODELS` is decommissioned by Groq; `llama-3.1-8b-instant` still works.
