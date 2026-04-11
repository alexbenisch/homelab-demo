#!/usr/bin/env python3
"""
Headless browser network debugger.
Navigates to a URL, waits for the page to settle, then reports:
  - All network requests and their status codes
  - Failed requests (4xx/5xx) highlighted
  - Browser console errors

Usage:
  python3 scripts/browser-debug.py <url> [wait_seconds]

Examples:
  python3 scripts/browser-debug.py https://keycloak-admin.tail55277.ts.net/admin/master/console/
  python3 scripts/browser-debug.py https://keycloak-admin.tail55277.ts.net/admin/master/console/ 15
"""

import sys
import asyncio
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost"
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 10

requests_log = []
console_errors = []


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=False)
        page = await context.new_page()

        # Capture every request/response
        async def on_response(response):
            requests_log.append({
                "status": response.status,
                "url": response.url,
                "method": response.request.method,
            })

        async def on_request_failed(request):
            requests_log.append({
                "status": "FAILED",
                "url": request.url,
                "method": request.method,
                "error": request.failure,
            })

        page.on("response", on_response)
        page.on("requestfailed", on_request_failed)
        page.on("console", lambda msg: console_errors.append(f"[{msg.type.upper()}] {msg.text}") if msg.type in ("error", "warning") else None)

        print(f"Navigating to {URL} (waiting {WAIT}s for JS to settle)...\n")
        try:
            await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Navigation error: {e}\n")

        await asyncio.sleep(WAIT)

        await browser.close()

    # --- Report ---
    failures = [r for r in requests_log if str(r["status"]).startswith(("4", "5")) or r["status"] == "FAILED"]
    ok = [r for r in requests_log if r not in failures]

    print(f"{'='*70}")
    print(f"FAILED REQUESTS ({len(failures)})")
    print(f"{'='*70}")
    for r in failures:
        print(f"  {r['status']}  {r['method']}  {r['url']}")

    print(f"\n{'='*70}")
    print(f"OK REQUESTS ({len(ok)})")
    print(f"{'='*70}")
    for r in ok:
        print(f"  {r['status']}  {r['method']}  {r['url']}")

    if console_errors:
        print(f"\n{'='*70}")
        print(f"CONSOLE ERRORS / WARNINGS ({len(console_errors)})")
        print(f"{'='*70}")
        for e in console_errors:
            print(f"  {e}")


asyncio.run(run())
