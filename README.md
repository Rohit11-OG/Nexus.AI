<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=220&text=NEXUS%20AIML%20Chatbot&fontAlign=50&fontAlignY=40&color=0:6a11cb,50:2575fc,100:00c6ff&fontColor=ffffff&animation=fadeIn" alt="Nexus AIML Banner" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=24&pause=1000&color=00C6FF&center=true&vCenter=true&width=900&lines=Classic+Rule-based+AIML+%2B+Modern+LLM+Fallback;Mini+Games%2C+Analytics%2C+Sessions%2C+Memory;Built+with+Flask+for+fast+local+deployment" alt="Typing animation" />
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python badge" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Framework-Flask-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask badge" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Engine-AIML-purple?style=for-the-badge" alt="AIML badge" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Fallback-LLM-success?style=for-the-badge" alt="LLM badge" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Status badge" /></a>
</p>

---

## What is Nexus?

`NEXUS AIML Chatbot` is a classic-meets-modern chatbot project:
- **Classic side:** AIML knowledge base for fast deterministic responses.
- **Crazy side:** optional LLM fallback for broader, richer conversations.
- **Extra layer:** web UI, analytics, mini-games, and modular config.

This project is ideal for learning chatbot architecture with both rules and generative intelligence in one app.

---

## Highlights

- AIML categories for greetings, science, jokes, stories, riddles, emotions, and more.
- Optional `llm_fallback.py` for responses when AIML confidence is low.
- Flask API + web frontend (`templates/`, `static/`) for interactive chatting.
- Built-in analytics view (`templates/analytics.html`) for insight into usage.
- Safety-focused environment configuration via `Settings.from_env()`.

---

## Project Structure

```text
.
|- app.py
|- engine.py
|- config.py
|- llm_fallback.py
|- requirements.txt
|- aiml/
|- templates/
|- static/
|- tests/
|- .env.example
```

---

## Quick Start

### 1) Clone and enter project

```bash
git clone https://github.com/Rohit11-OG/Nexus.AI.git
cd Nexus.AI
```

### 2) Create virtual environment

```bash
python -m venv .venv
```

Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure env

```bash
copy .env.example .env
```

Update `.env` with your values, especially `SECRET_KEY` and optional LLM settings.

### 5) Run app

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

---

## Environment Variables

Environment parsing is centralized in `config.py` through `Settings.from_env()`.

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key (required for production) | - |
| `CORS_ORIGINS` | Comma-separated allowed origins for `/api/*` | empty |
| `FLASK_DEBUG` | Debug mode | `false` |
| `HOST` | Bind host | `127.0.0.1` |
| `PORT` | Bind port | `5000` |
| `ENGINE_MAX_SESSIONS` | Session-engine cache size | `200` |
| `LOG_LEVEL` | Application logging level | `INFO` |

---

## Testing

Run smoke tests:

```bash
python -m unittest tests/test_api.py
```

---

## Screenshots / Demo (Optional)

Add your own screenshots or GIF demo here:

```markdown
![Chat UI](docs/images/chat-ui.png)
![Analytics](docs/images/analytics.png)
```

---

## Tech Stack

- **Backend:** Flask, Python
- **Chat logic:** AIML + optional LLM fallback
- **Frontend:** HTML, CSS, JavaScript
- **Testing:** Python unittest

---

## Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/amazing-update`
3. Commit changes: `git commit -m "Add amazing update"`
4. Push branch: `git push origin feature/amazing-update`
5. Open a Pull Request

---

## License

Add your license details here (for example, MIT).

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&text=Thanks%20for%20visiting%20Nexus.AI&fontColor=ffffff&color=0:00c6ff,100:6a11cb&height=80&animation=twinkling" alt="Footer banner" />
</p>
