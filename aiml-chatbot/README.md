# NEXUS AIML Chatbot

Flask-based AIML chatbot with optional LLM fallback, mini-games, and analytics.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set values you need.
4. Start app:
   - `python app.py`

The default URL is `http://127.0.0.1:5000`.

## Safety-focused configuration

Environment parsing is centralized in `config.py` via `Settings.from_env()`.

- `SECRET_KEY`: Flask session signing key (required for production).
- `CORS_ORIGINS`: comma-separated allowed origins for `/api/*`.
- `FLASK_DEBUG`: `true/false` (default: `false`).
- `HOST`: bind host (default: `127.0.0.1`).
- `PORT`: bind port (default: `5000`).
- `ENGINE_MAX_SESSIONS`: in-memory session-engine cache size (default: `200`).
- `LOG_LEVEL`: logging level (default: `INFO`).

## Tests

Run API smoke tests:

- `python -m unittest tests/test_api.py`
