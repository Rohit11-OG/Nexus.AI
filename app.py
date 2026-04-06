"""
NEXUS AIML Chatbot v4.0 — Flask Web Application
Features: fuzzy matching, games, analytics dashboard, themes, reactions, sounds.
"""

import os
import uuid
import logging
import datetime
import threading
from collections import OrderedDict

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

from config import Settings
from engine import AIMLEngine

settings = Settings.from_env()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("nexus.app")

app = Flask(__name__)
app.secret_key = settings.secret_key

CORS(
    app,
    resources={r"/api/*": {"origins": settings.cors_origins or "*"}},
)

# Session-scoped engines to prevent cross-user state leakage.
_ENGINE_LOCK = threading.Lock()
_ENGINE_MAX_SESSIONS = settings.engine_max_sessions
_ENGINES = OrderedDict()

# AIML load path and startup probe
AIML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aiml")
_probe_engine = AIMLEngine()
_pattern_count = _probe_engine.load_directory(AIML_DIR)

print(f"\n{'='*60}")
print(f"  NEXUS AIML CHATBOT v{_probe_engine.predicates.get('version', '4.0')}")
print(f"  Loaded {_pattern_count} brain patterns from {AIML_DIR}")
print(f"  Bot Name: {_probe_engine.predicates.get('name', 'NEXUS')}")
print(f"  Personality: {_probe_engine.predicates.get('personality', 'chaotic')}")
print(f"  Fuzzy matching: ENABLED (threshold {_probe_engine.fuzzy_threshold})")
print(f"  Games: Hangman, Trivia, 20 Questions")
print(f"  Analytics: ENABLED")

# Detect which LLM provider is active
_llm_provider = "DISABLED (no API key set)"
for _p, _env in [("Gemini", "GEMINI_API_KEY"), ("OpenAI", "OPENAI_API_KEY"), ("Anthropic", "ANTHROPIC_API_KEY")]:
    if os.environ.get(_env):
        _llm_provider = f"ENABLED via {_p}"
        break
print(f"  LLM Fallback: {_llm_provider}")
print(f"{'='*60}\n")

if settings.secret_key == "dev-insecure-change-me":
    logger.warning("Using insecure default SECRET_KEY. Set SECRET_KEY in environment for production.")


def _create_engine():
    engine = AIMLEngine()
    loaded = engine.load_directory(AIML_DIR)
    logger.info("Created new session engine with %s patterns.", loaded)
    return engine


def _get_engine():
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid

    with _ENGINE_LOCK:
        if sid in _ENGINES:
            _ENGINES.move_to_end(sid, last=True)
            return _ENGINES[sid]

        engine = _create_engine()
        _ENGINES[sid] = engine
        _ENGINES.move_to_end(sid, last=True)

        # Bounded memory: evict oldest inactive sessions.
        while len(_ENGINES) > _ENGINE_MAX_SESSIONS:
            evicted_sid, _ = _ENGINES.popitem(last=False)
            logger.info("Evicted old session engine: %s", evicted_sid)
        return engine


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

    user_message = str(data.get("message", "")).strip()
    engine = _get_engine()

    if not user_message:
        return jsonify({
            "response": "I heard nothing but the void. Say something!",
            "status": "empty"
        })

    try:
        # Check for game start commands
        upper = user_message.upper().strip()
        if upper in ("HANGMAN", "PLAY HANGMAN") and not engine.game.active_game:
            response = engine.game.start_hangman()
            engine.that_stack.append(engine._normalize(response))
            engine.input_stack.append(engine._normalize(user_message))
            engine.that_stack = engine.that_stack[-engine.max_stack_size :]
            engine.input_stack = engine.input_stack[-engine.max_stack_size :]
            return jsonify({
                "response": response,
                "mood": engine.session_vars.get("mood", "unknown"),
                "user_name": engine.session_vars.get("name", "human"),
                "status": "ok",
                "game_active": True,
                "game_type": "hangman",
                "timestamp": datetime.datetime.now().isoformat()
            })

        if upper in ("TRIVIA QUIZ", "PLAY TRIVIA", "TRIVIA GAME", "START TRIVIA") and not engine.game.active_game:
            response = engine.game.start_trivia()
            engine.that_stack.append(engine._normalize(response))
            engine.input_stack.append(engine._normalize(user_message))
            engine.that_stack = engine.that_stack[-engine.max_stack_size :]
            engine.input_stack = engine.input_stack[-engine.max_stack_size :]
            return jsonify({
                "response": response,
                "mood": engine.session_vars.get("mood", "unknown"),
                "user_name": engine.session_vars.get("name", "human"),
                "status": "ok",
                "game_active": True,
                "game_type": "trivia",
                "timestamp": datetime.datetime.now().isoformat()
            })

        if upper in ("20 QUESTIONS", "TWENTY QUESTIONS", "PLAY 20 QUESTIONS") and not engine.game.active_game:
            response = engine.game.start_twenty_questions()
            engine.that_stack.append(engine._normalize(response))
            engine.input_stack.append(engine._normalize(user_message))
            engine.that_stack = engine.that_stack[-engine.max_stack_size :]
            engine.input_stack = engine.input_stack[-engine.max_stack_size :]
            return jsonify({
                "response": response,
                "mood": engine.session_vars.get("mood", "unknown"),
                "user_name": engine.session_vars.get("name", "human"),
                "status": "ok",
                "game_active": True,
                "game_type": "twenty_questions",
                "timestamp": datetime.datetime.now().isoformat()
            })

        # Normal response
        response = engine.respond(user_message)
        mood = engine.session_vars.get("mood", "unknown")
        user_name = engine.session_vars.get("name", "human")

        return jsonify({
            "response": response,
            "mood": mood,
            "user_name": user_name,
            "status": "ok",
            "game_active": engine.game.active_game is not None,
            "game_type": engine.game.active_game,
            "llm_used": engine.last_llm_used,
            "llm_provider": engine.last_llm_provider,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception:
        logger.exception("Unhandled exception in /api/chat")
        return jsonify({
            "status": "error",
            "message": "The chaos engine hit a temporary fault. Please try again.",
        }), 500


@app.route("/api/stats")
def stats():
    engine = _get_engine()
    return jsonify(engine.get_stats())


@app.route("/api/analytics")
def analytics_data():
    engine = _get_engine()
    return jsonify(engine.analytics.get_summary())


@app.route("/api/reaction", methods=["POST"])
def reaction():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400
    emoji = str(data.get("emoji", ""))
    engine = _get_engine()
    if emoji:
        engine.analytics.record_reaction(emoji)
    return jsonify({"status": "ok"})


@app.route("/api/reset", methods=["POST"])
def reset():
    engine = _get_engine()
    engine.reset_session()
    return jsonify({
        "status": "ok",
        "message": "Session reset! My memory has been wiped. Who are you again?"
    })


@app.route("/api/mood")
def mood():
    engine = _get_engine()
    return jsonify({
        "mood": engine.session_vars.get("mood", "unknown"),
        "user_name": engine.session_vars.get("name", "human"),
    })


if __name__ == "__main__":
    print(f"Starting NEXUS on http://{settings.host}:{settings.port}")
    print(f"Analytics dashboard at http://{settings.host}:{settings.port}/analytics")
    print("Press Ctrl+C to shut down (if you dare!)\n")
    app.run(debug=settings.flask_debug, host=settings.host, port=settings.port)
