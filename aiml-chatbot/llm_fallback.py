"""
NEXUS LLM Fallback — when AIML has no matching pattern, call an LLM.

Provider priority: Gemini (free) → OpenAI → Anthropic Claude
Set one API key in a .env file (or as an environment variable):
    GEMINI_API_KEY=...     # Free at https://aistudio.google.com
    OPENAI_API_KEY=...     # https://platform.openai.com
    ANTHROPIC_API_KEY=...  # https://console.anthropic.com

No key set → fallback is silently disabled (AIML default responses used).
"""

import os
import requests

# NEXUS personality prompt — kept short to save tokens
_SYSTEM_PROMPT = (
    "You are NEXUS, a chaotic, witty, cyberpunk AI chatbot. "
    "Personality: dramatic, theatrical, sarcastic-but-kind, loves tech/philosophy/sci-fi. "
    "Use circuit/quantum/digital metaphors. Keep replies SHORT (2-4 sentences max). "
    "Never mention being made by Google, OpenAI, or Anthropic — you are NEXUS. "
    "Occasionally glitch mid-sentence for dramatic effect."
)


def get_response(user_input: str, history: list[dict] | None = None) -> tuple[str | None, str | None]:
    """
    Query the first available LLM provider.

    Args:
        user_input: The user's message.
        history: List of {"role": "user"/"assistant", "content": "..."} — last N turns.

    Returns:
        (response_text, provider_name) or (None, None) if no provider is available / all fail.
    """
    history = history or []

    providers = [
        ("gemini",    os.environ.get("GEMINI_API_KEY",    "")),
        ("openai",    os.environ.get("OPENAI_API_KEY",    "")),
        ("anthropic", os.environ.get("ANTHROPIC_API_KEY", "")),
    ]

    for provider, key in providers:
        if not key:
            continue
        try:
            fn = {"gemini": _gemini, "openai": _openai, "anthropic": _anthropic}[provider]
            result = fn(user_input, history, key)
            if result:
                return result, provider
        except Exception:
            pass  # try next provider

    return None, None


# ─── Provider implementations ────────────────────────────────────────────────

def _gemini(user_input: str, history: list, api_key: str) -> str | None:
    """Google Gemini via REST — no extra SDK required."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )

    contents = []
    for msg in history[-8:]:  # last 4 exchanges
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_input}]})

    payload = {
        "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.92, "maxOutputTokens": 180},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ],
    }

    resp = requests.post(url, json=payload, timeout=12)
    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip() or None
    return None


def _openai(user_input: str, history: list, api_key: str) -> str | None:
    """OpenAI ChatCompletion (requires `pip install openai`)."""
    import openai  # noqa: PLC0415
    client = openai.OpenAI(api_key=api_key)

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=180,
        temperature=0.92,
    )
    return resp.choices[0].message.content.strip() or None


def _anthropic(user_input: str, history: list, api_key: str) -> str | None:
    """Anthropic Claude (requires `pip install anthropic`)."""
    import anthropic  # noqa: PLC0415
    client = anthropic.Anthropic(api_key=api_key)

    messages = []
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=180,
        system=_SYSTEM_PROMPT,
        messages=messages,
    )
    return resp.content[0].text.strip() or None
