import os
from dataclasses import dataclass


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; environment variables can be set externally.
    pass


def env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def env_list(name):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_int(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    secret_key: str
    cors_origins: list[str]
    flask_debug: bool
    host: str
    port: int
    engine_max_sessions: int
    log_level: str

    @classmethod
    def from_env(cls):
        return cls(
            secret_key=os.environ.get("SECRET_KEY", "dev-insecure-change-me"),
            cors_origins=env_list("CORS_ORIGINS"),
            flask_debug=env_bool("FLASK_DEBUG", False),
            host=os.environ.get("HOST", "127.0.0.1"),
            port=env_int("PORT", 5000),
            engine_max_sessions=max(1, env_int("ENGINE_MAX_SESSIONS", 200)),
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
