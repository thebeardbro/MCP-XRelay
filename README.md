# MCP-XRelay

> **Automated Cybersecurity & Hardware News Poster for X (Twitter)**
>
> Fetches the latest security and enterprise-hardware headlines from multiple RSS feeds, rewrites them using a local OpenAI-compatible LLM, and posts concise updates to X every 5 minutes—completely offline, API-free, and rate-limit-resilient.

---

## ✨ Key Features

| ⚙️               | Description                                                                    |
|------------------|--------------------------------------------------------------------------------|
| **Async RSS**    | Non-blocking RSS fetch + thread-pool parsing for fast performance              |
| **Local LLM**    | Works with any local OpenAI-compatible endpoint (LM Studio, Ollama, llama.cpp) |
| **Three Voices** | Rotating personas: Friendly Expert, Thought-Leader, Witty Advisor               |
| **Smart Tags**   | Global `#TechNews` + category tags (security, hardware, general)               |
| **CTA Links**    | 30 % chance to append configurable call-to-action links                        |
| **Retries**      | Exponential back-off on LLM calls & posting (tenacity)                         |
| **Session Reuse**| Single Playwright browser context reused for all posts                         |
| **Deduplication**| SQLite database prevents duplicate tweets                                       |

---

## 🖥 Prerequisites

| Tool        | Version (tested)                    | Purpose                 |
|-------------|-------------------------------------|-------------------------|
| Python      | 3.9+                                | Runtime                 |
| pip / venv  | latest                              | Dependency isolation    |
| Playwright  | ≥ 1.40                              | Browser automation      |
| Local LLM   | Any OpenAI-API-compatible server    | LLM inference endpoint  |

> **Default LLM model:** `gemma-3-1b-it-qat`. Adjust `LLM_MODEL` if needed.

---

## 🔧 Environment Preparation

1. **Clone the repo**
   ```bash
   git clone https://github.com/thebeardbro/MCP-XRelay.git
   cd MCP-XRelay
   ```

2. **Create & activate virtualenv**
   ```bash
   python -m venv .venv
   # macOS/Linux: source .venv/bin/activate
   # PowerShell: .\.venv\Scripts\Activate.ps1
   # CMD:      .\.venv\Scripts\activate.bat
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

4. **Create `.env`** (see `.env.example`)
5. **Capture X session** (one-liner below)
6. **Run the bot**: `python bot.py`

---

## ☕ Support

If you find MCP-XRelay helpful, please [buy me a coffee](https://buymeacoffee.com/thebeardbro) to support development.

---

## 📄 License

MIT License © 2025 [@thebeardbro](https://github.com/thebeardbro)
