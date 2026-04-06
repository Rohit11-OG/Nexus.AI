<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=250&text=NEXUS.AI%20%7C%20V2%20ULTRA%20CRAZY&fontAlign=50&fontAlignY=40&color=0:ff0080,25:7928ca,50:2afadf,75:00c6ff,100:005bea&fontColor=ffffff&animation=blinking" alt="Nexus AI Ultra Header" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Orbitron&weight=700&size=25&pause=900&color=00F7FF&center=true&vCenter=true&random=false&width=1000&lines=SYSTEM+ONLINE:+NEXUS.AI+CHAT+CORE+INITIALIZED;AIML+RULE+ENGINE+%2B+LLM+FALLBACK+FUSION;MINI-GAMES+%7C+ANALYTICS+%7C+SESSION+MEMORY+%7C+WEB+UI;WELCOME+TO+THE+CYBER+CHAT+ZONE" alt="Typing Line" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Mode-Neon%20Classic%20x%20Crazy-111111?style=for-the-badge&logo=github&logoColor=white" alt="Mode Badge" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge" />
  <img src="https://img.shields.io/badge/Flask-API-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask Badge" />
  <img src="https://img.shields.io/badge/AIML-Core-8A2BE2?style=for-the-badge" alt="AIML Badge" />
  <img src="https://img.shields.io/badge/LLM-Fallback-00C853?style=for-the-badge" alt="LLM Badge" />
  <img src="https://img.shields.io/badge/Status-LIVE-00E5FF?style=for-the-badge" alt="Status Badge" />
</p>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=Rohit11-OG&label=Profile%20Views&color=0e75b6&style=flat" alt="Profile views" />
  <img src="https://img.shields.io/github/stars/Rohit11-OG/Nexus.AI?style=flat&color=yellow" alt="Stars" />
  <img src="https://img.shields.io/github/forks/Rohit11-OG/Nexus.AI?style=flat&color=blueviolet" alt="Forks" />
  <img src="https://img.shields.io/github/last-commit/Rohit11-OG/Nexus.AI?style=flat&color=brightgreen" alt="Last Commit" />
</p>

---

## Cyber Intro

Welcome to **NEXUS.AI V2 ULTRA CRAZY**: a chatbot where old-school deterministic AIML meets modern LLM fallback.

- **Classic Brain:** structured AIML categories for predictable, fast responses.
- **Crazy Brain:** dynamic fallback via `llm_fallback.py` when rules are not enough.
- **Battle Arena:** mini-games, analytics dashboard, API endpoints, and clean Flask delivery.

---

## Why This Hits Different

- Rule engine + generative fallback in one architecture.
- Large AIML topic spread: greetings, jokes, science, stories, riddles, emotions.
- Built-in web experience from `templates/` and `static/`.
- Analytics panel for usage visibility.
- Centralized safe config loading with `Settings.from_env()` in `config.py`.

---

## System Blueprint

```text
NEXUS.AI
|- app.py               # Flask entrypoint
|- engine.py            # Core chat + AIML orchestration
|- llm_fallback.py      # Optional generative fallback
|- config.py            # Environment + runtime settings
|- requirements.txt
|- aiml/                # Knowledge brain
|- templates/           # HTML views
|- static/              # CSS/JS assets
|- tests/               # API tests
|- .env.example
```

---

## Boot Sequence

### 1) Clone repo

```bash
git clone https://github.com/Rohit11-OG/Nexus.AI.git
cd Nexus.AI
```

### 2) Create virtual env

```bash
python -m venv .venv
```

Windows PowerShell:

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

### 4) Configure runtime secrets

Windows:

```powershell
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Then edit `.env` and set your values (`SECRET_KEY`, optional LLM keys/settings).

### 5) Launch

```bash
python app.py
```

Open in browser: `http://127.0.0.1:5000`

---

## Runtime Config Matrix

| Variable | What it controls | Default |
|---|---|---|
| `SECRET_KEY` | Flask session signing key (must set in production) | - |
| `CORS_ORIGINS` | Allowed origins for `/api/*` | empty |
| `FLASK_DEBUG` | Debug mode toggle | `false` |
| `HOST` | Server bind host | `127.0.0.1` |
| `PORT` | Server bind port | `5000` |
| `ENGINE_MAX_SESSIONS` | Session cache size | `200` |
| `LOG_LEVEL` | Application log verbosity | `INFO` |

---

## Test Protocol

```bash
python -m unittest tests/test_api.py
```

---

## Drop Your Demo

Add GIFs/screenshots to make this page even crazier:

```markdown
![Nexus Chat Demo](docs/images/chat-demo.gif)
![Analytics Panel](docs/images/analytics.png)
```

---

## Stack

<p>
  <img src="https://skillicons.dev/icons?i=python,flask,html,css,js,git,github,vscode" alt="Tech Icons" />
</p>

---

## Contribution Mode

1. Fork this repository
2. Create a branch: `git checkout -b feature/next-upgrade`
3. Commit changes: `git commit -m "Add next upgrade"`
4. Push branch: `git push origin feature/next-upgrade`
5. Open a pull request

---

## License

Add a license file (`LICENSE`) and update this section (MIT recommended if you want open usage).

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=90&section=footer&text=END%20OF%20TRANSMISSION%20%7C%20NEXUS.AI&fontSize=24&color=0:00f5d4,100:00bbf9&fontColor=0b0f19&animation=twinkling" alt="Footer" />
</p>
