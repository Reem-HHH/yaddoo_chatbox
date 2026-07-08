# Yaddoo (مجلس يَدّوه)

Arabic/Emirati grandma chatbot for kids. A Flask backend proxies chat requests to
the Groq API; a static frontend provides the RTL chat UI.

- `backend/app.py` — Flask API (`/api/chat`, `/health`, `/`). Defaults to port `3000`.
- Repo root — static frontend: `index.html`, `app.js`, `styles.css`, `bg_majlis.png`,
  and `assets/`. These live at the root so GitHub Pages serves the app at its root URL.

## Cursor Cloud specific instructions

Services (run each in its own terminal; leave both running for local dev):

| Service  | Command | Port | Notes |
| -------- | ------- | ---- | ----- |
| Backend  | `set -a; . /workspace/backend/.env; set +a; cd backend && /workspace/.venv/bin/python app.py` | 3000 | Flask dev server (`debug=True`). |
| Frontend | `cd /workspace && /workspace/.venv/bin/python -m http.server 5500` | 5500 | Serves the static files from the repo root. |

Open the app at `http://localhost:5500/index.html`. There is no build step and no
lint/test suite in this repo.

Non-obvious caveats:
- Env loading: `app.py` calls `load_dotenv(BASE_DIR / ".env")`, i.e. it reads
  `backend/.env` — NOT the repo-root `/workspace/.env`. Put a valid `GROQ_API_KEY`
  (and optionally `GROQ_MODELS`) in `backend/.env` (git-ignored). `GET /health`
  returns `"has_key": true` once the key is loaded.
- The `GROQ_API_KEY` secret is injected as an env var, but the persistent tmux
  server can predate the injection and may not have it. Writing the key to
  `backend/.env` is the reliable path; sourcing it (`set -a; . backend/.env`) also
  guarantees it overrides any stale value.
- The key committed in the repo-root `/workspace/.env` is INVALID (Groq returns
  `401`); do not rely on it. Use the injected `GROQ_API_KEY` secret instead.
- `mixtral-8x7b-32768` in the default `GROQ_MODELS` is decommissioned by Groq; use
  `llama-3.1-8b-instant` (the app auto-falls back to it anyway).
- The frontend hardcodes its API base: on `localhost`/`127.0.0.1` it calls
  `http://localhost:3000`, otherwise the public Render URL. Keep the backend on
  port 3000 for local testing.
- Rule-based replies (greetings, small talk, very short/garbled input) are answered
  locally without calling Groq — useful for smoke-testing without a valid key.
