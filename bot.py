#!/usr/bin/env python3
"""
MCP-XRelay — Automated Cybersecurity & Hardware News Poster for X
================================================================
Fetches security and hardware headlines via RSS, rewrites with a local OpenAI-compatible LLM,
and posts updates to X every 5 minutes.
"""

import asyncio
import datetime as dt
import logging
import os
import random
import re
import sqlite3
import sys
from typing import Any, List

import feedparser
import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, stop_after_attempt, wait_exponential

# Configuration
FEED_URLS: List[str] = os.getenv(
    "FEED_URLS",
    ",".join([
        "https://feeds.feedburner.com/TheHackersNews",
        "https://threatpost.com/feed/",
        "https://securityaffairs.co/wordpress/feed",
        "https://isc.sans.edu/rssfeed.xml",
        "https://www.theregister.com/security/headlines.rss",
        "https://www.servethehome.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/gadgets",
        "https://techcrunch.com/hardware/feed/",
    ])
).split(",")
DB_PATH = os.getenv("DB_PATH", "cybersec_news.db")
AUTH_STATE = os.getenv("AUTH_STATE", "state.json")
CHAR_LIMIT = int(os.getenv("CHAR_LIMIT", "280"))
LM_API_URL = os.getenv("LM_API_URL", "http://127.0.0.1:1234/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma-3-1b-it-qat")
CTA_CHANCE = int(os.getenv("CTA_CHANCE", "30"))
CTA_LINKS: List[str] = (
    os.getenv("CTA_LINKS")
    and os.getenv("CTA_LINKS").split(",")
    or [
        "https://example.com/contact/",
        "https://example.com/services/",
    ]
)

DEFAULT_HASHTAGS: List[str] = ["#TechNews"]
HASHTAG_CATEGORIES = {
    "security": ["#CyberSecurity", "#ThreatIntel", "#InfoSec", "#Malware"],
    "hardware": ["#EnterpriseHardware", "#DataCenter", "#Networking", "#TechHardware"],
    "general": ["#ITServices", "#Consulting", "#Innovation"],
}

SEC_DOMAINS = ["thehackersnews", "threatpost", "securityaffairs", "sans.edu", "theregister.com"]
HW_DOMAINS = ["servethehome.com", "arstechnica.com", "techcrunch.com"]

PERSONAS = [
    {
        "name": "Friendly Expert",
        "system": (
            "You are a friendly cybersecurity consultant. Write a single engaging sentence explaining why this news matters and offer a practical takeaway. End with the link."
        ),
    },
    {
        "name": "Thought-Leader",
        "system": (
            "Provide a concise insight linking this headline to a broader trend and suggest proactive action. End with the link."
        ),
    },
    {
        "name": "Witty Advisor",
        "system": (
            "Craft a clever, professional one-liner that summarizes the news and nudges readers to stay secure. End with the link."
        ),
    },
]

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Database initialization
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            link TEXT UNIQUE,
            title TEXT,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn

# Fetch recent feed entries
async def _parse(url: str):
    return await asyncio.to_thread(feedparser.parse, url)

async def fetch_items() -> List[dict]:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)
    items: List[dict] = []
    feeds = await asyncio.gather(*[_parse(u) for u in FEED_URLS], return_exceptions=True)
    for feed in feeds:
        if isinstance(feed, Exception):
            logging.warning("Feed error: %s", feed)
            continue
        for e in getattr(feed, "entries", []):
            pub = e.get("published_parsed") or e.get("updated_parsed")
            if pub and dt.datetime(*pub[:6], tzinfo=dt.timezone.utc) < cutoff:
                continue
            title, link = e.get("title", "").strip(), e.get("link", "").strip()
            if title and link:
                items.append({"title": title, "link": link})
    logging.info("Fetched %d items", len(items))
    return items

# Tweet generator

def _maybe_cta(current_len: int) -> str:
    if random.randint(1, 100) > CTA_CHANCE:
        return ""
    link = random.choice(CTA_LINKS)
    return f" {link}" if current_len + len(link) + 1 <= CHAR_LIMIT else ""

async def generate_tweet(title: str, link: str) -> str:
    persona = random.choice(PERSONAS)
    system_msg = {"role": "system", "content": persona["system"]}
    user_msg = {"role": "user", "content": f"Headline: '{title}'\nLink: {link}"}
    domain = link.lower()
    if any(d in domain for d in SEC_DOMAINS):
        category = "security"
    elif any(d in domain for d in HW_DOMAINS):
        category = "hardware"
    else:
        category = "general"
    tags = DEFAULT_HASHTAGS + random.sample(HASHTAG_CATEGORIES[category], 2)
    hash_block = " " + " ".join(tags)
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=8),
            retry=retry_if_exception_type(Exception),
        ):
            with attempt:
                r = requests.post(
                    LM_API_URL,
                    json={
                        "model": LLM_MODEL,
                        "messages": [system_msg, user_msg],
                        "temperature": 0.8,
                        "max_tokens": 120,
                        "top_p": 0.95,
                    },
                    timeout=(3, 10),
                )
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"].strip()
                text = re.sub(r"^(okay|ok|sure|here(?:'s| is)|tweet[:,]?)[\s,:-]+", "", text, flags=re.I)
                text = " ".join(text.split())
                cta = _maybe_cta(len(text) + len(link) + len(hash_block) + 2)
                reserve = len(link) + len(hash_block) + len(cta) + 2
                max_len = CHAR_LIMIT - reserve
                if len(text) > max_len:
                    punct = max((text.rfind(p, 0, max_len) for p in ".!?"), default=-1)
                    if punct >= max_len * 0.5:
                        text = text[: punct + 1]
                    else:
                        cut = text[:max_len]
                        text = cut[: cut.rfind(" ")] if " " in cut else cut
                        text = text.rstrip(".,!?") + "..."
                return f"{text} {link}{cta}{hash_block}"
    except RetryError:
        logging.error("LLM unavailable – using fallback")
    return f"{title} {link}{hash_block}"

# Playwright poster
class XPoster:
    def __init__(self) -> None:
        self.pw: Any | None = None
        self.browser = None
        self.page = None

    async def __aenter__(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=True)
        ctx = await self.browser.new_context(storage_state=AUTH_STATE)
        self.page = await ctx.new_page()
        await self.page.goto("https://x.com", wait_until="domcontentloaded")
        try:
            await self.page.click('button:has-text("Accept all cookies")', timeout=4000)
        except Exception:
            pass
        return self

    async def __aexit__(self, *_):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

    async def post(self, text: str) -> bool:
        for attempt in range(3):
            try:
                await self.page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
                await self.page.fill('div[role="textbox"]', text)
                await self.page.keyboard.press("Control+Enter")
                await asyncio.sleep(2)
                return True
            except PlaywrightTimeoutError:
                logging.warning("post attempt %d failed", attempt + 1)
        return False

# Job runner
async def job(conn: sqlite3.Connection, poster: XPoster) -> None:
    cursor = conn.cursor()
    items = await fetch_items()
    for item in items:
        if cursor.execute("SELECT 1 FROM posts WHERE link=?", (item["link"],)).fetchone():
            continue  # already posted
        tweet = await generate_tweet(item["title"], item["link"])
        logging.info("Tweet => %s", tweet)
        if await poster.post(tweet):
            cursor.execute(
                "INSERT INTO posts(link,title) VALUES(?,?)",
                (item["link"], item["title"])
            )
            logging.info("Posted & saved")
        else:
            logging.error("Failed to post tweet")

# Main loop
async def main() -> None:
    conn = init_db()
    async with XPoster() as poster:
        try:
            while True:
                loop_start = dt.datetime.now(dt.timezone.utc)
                await job(conn, poster)
                elapsed = (dt.datetime.now(dt.timezone.utc) - loop_start).total_seconds()
                await asyncio.sleep(max(0, 300 - elapsed))
        finally:
            conn.close()

if __name__ == "__main__":
    if sys.version_info < (3, 9):
        sys.exit("Python 3.9+ required")
    asyncio.run(main())
