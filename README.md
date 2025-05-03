# MCP‑XRelay

> **Automated Cybersecurity & Hardware News Poster for X (Twitter)**
>
> Fetches the latest security and enterprise‑hardware headlines from multiple RSS feeds, rewrites them using a local OpenAI‑compatible LLM, and posts concise updates to X every 5 minutes—completely offline, API‑free, and rate‑limit‑resilient.

---

## ✨ Key Features

| ⚙️                | Description                                                                    |
| ----------------- | ------------------------------------------------------------------------------ |
| **Async RSS**     | Non‑blocking RSS fetch + thread‑pool parsing for fast performance              |
| **Local LLM**     | Works with any local OpenAI‑compatible endpoint (LM Studio, Ollama, llama.cpp) |
| **Three Voices**  | Rotating personas: Friendly Expert, Thought‑Leader, Witty Advisor              |
| **Smart Tags**    | Global `#TechNews` + category tags (security, hardware, general)               |
| **CTA Links**     | 30 % chance to append configurable call‑to‑action links                        |
| **Retries**       | Exponential back‑off on LLM calls & posting (tenacity)                         |
| **Session Reuse** | Single Playwright browser context reused for all posts                         |
| **Deduplication** | SQLite database prevents duplicate tweets                                      |

---

## 🖥 Prerequisites

| Tool       | Version (tested)                 | Purpose                |
| ---------- | -------------------------------- | ---------------------- |
| Python     |  3.9+                            | Runtime                |
| pip / venv | latest                           | Dependency isolation   |
| Playwright |  ≥ 1.40                          | Browser automation     |
| Local LLM  | Any OpenAI‑API‑compatible server | LLM inference endpoint |

> **Default LLM model:** `gemma-3-1b-it-qat`. Adjust `LLM_MODEL` if needed.

---

## 🔧 Environment Preparation

### 1 — Clone the Repository

```bash
git clone https://github.com/thebeardbro/MCP-XRelay.git
cd MCP-XRelay
```

### 2 — Create & Activate a Virtual Environment *(recommended)*

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Windows (CMD)
.\.venv\Scripts\activate.bat
```

### 3 — Install Dependencies & Playwright Browsers

```bash
pip install -r requirements.txt
playwright install               # one-time browser download (~120 MB)
```

### 4 — Configure Environment Variables

Create a `.env` file in the project root with the following:

```env
# RSS feed URLs (comma‑separated)
FEED_URLS=https://feeds.feedburner.com/TheHackersNews,https://threatpost.com/feed/,https://securityaffairs.co/wordpress/feed

# Local LLM settings\LM_API_URL=http://127.0.0.1:1234/v1/chat/completions
LLM_MODEL=gemma-3-1b-it-qat

# Tweet configuration
CHAR_LIMIT=280
CTA_CHANCE=30

# Playwright session file
AUTH_STATE=state.json

# Database file\mDB_PATH=cybersec_news.db

# Optional CTA links override
CTA_LINKS=https://example.com/contact/,https://example.com/services/
```

### 5 — Capture X (Twitter) Session

**One-liner** to open Chromium, log in to X, and save cookies to `state.json`:

```bash
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=False); ctx=b.new_context(); page=ctx.new_page(); page.goto('https://x.com/login'); input('Log in, then press Enter…'); ctx.storage_state(path='state.json'); b.close(); p.stop()"
```

> This step must be done once before running the bot.

### 6 — Launch the Bot

```bash
python bot.py   # or python mcp_xrelay.py if renamed
```

The bot will run continuously, fetching feeds, generating tweets, and posting every 5 minutes. Use **Ctrl +C** to stop.

---

## ⚙️ Runtime Configuration

Override any setting via environment variables or inline:

```bash
FEED_URLS=https://myfeed.com/rss CTA_CHANCE=0 python bot.py
```

### Important Variables

| Variable     | Purpose                                |
| ------------ | -------------------------------------- |
| `FEED_URLS`  | Comma‑separated list of RSS feed URLs  |
| `LM_API_URL` | Local LLM endpoint URL                 |
| `LLM_MODEL`  | Model name for LLM inference           |
| `CHAR_LIMIT` | Maximum tweet length                   |
| `CTA_CHANCE` | Percent chance to include a CTA link   |
| `AUTH_STATE` | Playwright session file (cookies)      |
| `DB_PATH`    | SQLite database path for tweet history |

---

## 📦 Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt && playwright install
ENV FEED_URLS="$(FEED_URLS)" \
    LM_API_URL=http://host.docker.internal:1234/v1/chat/completions \
    LLM_MODEL=gemma-3-1b-it-qat
CMD ["python", "bot.py"]
```

> Mount your `.env` and `state.json` as volumes.

---

## 🧪 Sample Output

```text
Patch Tuesday drops 60+ fixes in MSMQ—patch now to stay safe. https://threatpost.com/... #TechNews #CyberSecurity #ThreatIntel
```

---

## 🤝 Contributing

1. Fork the repo & create a branch
2. Make changes & run `pre-commit run --all-files`
3. Submit a pull request with a descriptive title

---

## ☕ Support

If MCP‑XRelay helps you, please:

* ⭐ Star the repository
* 🐦 Share on X
* ☕ [Buy me a coffee](https://buymeacoffee.com/thebeardbro)

---

## 📄 License

MIT License © 2025 [@thebeardbro](https://github.com/thebeardbro)
