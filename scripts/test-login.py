#!/usr/bin/env python3
"""
End-to-end login test for oauth2-proxy + Keycloak OIDC flows.

Tests the full browser login journey:
  1. Visit protected URL → redirected to Keycloak login
  2. Fill in credentials and submit
  3. Confirm redirect back to app and page loads correctly

Usage:
  python3 scripts/test-login.py <url> <username> <password> [--path /tenant/]

Examples:
  python3 scripts/test-login.py https://nodeposit.kubetest.uk tenant1 'Tenant1Pass!'
  python3 scripts/test-login.py https://nodeposit.kubetest.uk tenant1 'Tenant1Pass!' --path /tenant/
  python3 scripts/test-login.py https://nodeposit.kubetest.uk landlord1 'Landlord1Pass!' --path /landlord/
"""

import sys
import asyncio
import argparse
from playwright.async_api import async_playwright

parser = argparse.ArgumentParser()
parser.add_argument("url",      help="Base URL of the app (e.g. https://nodeposit.kubetest.uk)")
parser.add_argument("username", help="Keycloak username")
parser.add_argument("password", help="Keycloak password")
parser.add_argument("--path",   default="/", help="Path to test (default: /)")
args = parser.parse_args()

TARGET = args.url.rstrip("/") + args.path
PASS_MARK  = "\033[92m[PASS]\033[0m"
FAIL_MARK  = "\033[91m[FAIL]\033[0m"
INFO_MARK  = "\033[94m[INFO]\033[0m"
STEP_MARK  = "\033[93m[STEP]\033[0m"

requests_log = []
console_errors = []

def log(mark, msg):
    print(f"{mark} {msg}")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=False)
        page = await context.new_page()

        page.on("response", lambda r: requests_log.append({
            "status": r.status, "url": r.url, "method": r.request.method
        }))
        page.on("requestfailed", lambda r: requests_log.append({
            "status": "NET_ERR", "url": r.url, "method": r.method, "error": r.failure
        }))
        page.on("console", lambda m: console_errors.append(f"[{m.type.upper()}] {m.text}")
                if m.type in ("error", "warning") else None)

        # ── Step 1: navigate to protected URL ──────────────────────────────
        log(STEP_MARK, f"Navigating to {TARGET}")
        try:
            await page.goto(TARGET, wait_until="networkidle", timeout=20000)
        except Exception as e:
            log(FAIL_MARK, f"Navigation error: {e}")
            await browser.close()
            sys.exit(1)

        current = page.url
        log(INFO_MARK, f"Landed on: {current}")

        # ── Step 2: detect Keycloak login form ────────────────────────────
        if "openid-connect/auth" in current or "auth/realms" in current:
            log(PASS_MARK, "Redirected to Keycloak login page")
        else:
            log(FAIL_MARK, f"Expected Keycloak redirect, got: {current}")
            await browser.close()
            sys.exit(1)

        # ── Step 3: fill credentials ──────────────────────────────────────
        log(STEP_MARK, f"Filling credentials for user: {args.username}")
        try:
            await page.wait_for_selector("#username", timeout=10000)
            await page.fill("#username", args.username)
            await page.fill("#password", args.password)
        except Exception as e:
            log(FAIL_MARK, f"Could not find login form fields: {e}")
            await browser.close()
            sys.exit(1)

        # ── Step 4: submit and wait for navigation ────────────────────────
        log(STEP_MARK, "Submitting login form")
        try:
            async with page.expect_navigation(wait_until="networkidle", timeout=20000):
                await page.click("#kc-login")
        except Exception as e:
            log(FAIL_MARK, f"Login submission failed: {e}")
            await browser.close()
            sys.exit(1)

        after_login = page.url
        log(INFO_MARK, f"After login: {after_login}")

        # ── Step 5: verify we are back on the app ─────────────────────────
        app_host = args.url.rstrip("/")
        if after_login.startswith(app_host) and "oauth2/callback" not in after_login:
            log(PASS_MARK, "Successfully authenticated — back on app")
        elif "oauth2/callback" in after_login:
            log(FAIL_MARK, f"Stuck on oauth2/callback — OIDC error during token exchange")
        elif "auth.kubetest.uk" in after_login:
            log(FAIL_MARK, f"Still on Keycloak — likely wrong credentials or form error")
            # Try to capture error message
            try:
                err = await page.inner_text(".alert-error", timeout=2000)
                log(INFO_MARK, f"Keycloak error message: {err.strip()}")
            except:
                pass
        else:
            log(FAIL_MARK, f"Unexpected URL after login: {after_login}")

        # ── Step 6: check page content ────────────────────────────────────
        try:
            title = await page.title()
            log(INFO_MARK, f"Page title: {title}")
        except:
            pass

        # ── Step 7: check for 500s ────────────────────────────────────────
        failures = [r for r in requests_log if str(r["status"]).startswith(("4", "5")) or r["status"] == "NET_ERR"]
        oauth_errors = [r for r in failures if "oauth2/callback" in r["url"]]
        other_errors = [r for r in failures if "oauth2/callback" not in r["url"]]

        if oauth_errors:
            log(FAIL_MARK, f"oauth2/callback errors ({len(oauth_errors)}):")
            for r in oauth_errors:
                log("      ", f"{r['status']}  {r['url'][:100]}")
        if other_errors:
            log(FAIL_MARK, f"Other HTTP errors ({len(other_errors)}):")
            for r in other_errors:
                log("      ", f"{r['status']}  {r['url'][:100]}")
        if not failures:
            log(PASS_MARK, "No HTTP errors during login flow")

        if console_errors:
            log(INFO_MARK, f"Browser console errors/warnings ({len(console_errors)}):")
            for e in console_errors:
                print(f"       {e}")

        await browser.close()

        # ── Summary ───────────────────────────────────────────────────────
        print()
        total = len(requests_log)
        fail_count = len(failures)
        print(f"Total requests: {total}  |  Failures: {fail_count}  |  Console issues: {len(console_errors)}")

asyncio.run(run())
