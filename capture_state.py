python - <<"PY"
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://x.com/login")
    input("Log into X manually, then press <Enter>…")
    ctx.storage_state(path="state.json")
    browser.close()
PY