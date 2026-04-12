#!/usr/bin/env python3
"""
End-to-end API test suite for the no-deposit app.

Uses Playwright for OIDC login (browser-based — direct access grants are
disabled on this Keycloak realm), then exercises every API endpoint with
the authenticated session cookies.

Each user gets an isolated browser context so sessions don't bleed.

Usage:
  python3 scripts/e2e-api-tests.py [BASE_URL] [--property-id N]

Examples:
  python3 scripts/e2e-api-tests.py
  python3 scripts/e2e-api-tests.py https://nodeposit.kubetest.uk
  python3 scripts/e2e-api-tests.py --property-id 1   # enables full CRUD flow

Options:
  --property-id N   Run the tenant→agent→landlord CRUD flow using
                    property N. The property must already exist.
                    Seed one with:
                      kubectl -n no-deposit run seed ... -- python manage.py seed_e2e

Exit code: 0 all pass, 1 any fail.
"""

import asyncio
import argparse
import json
import sys

from playwright.async_api import async_playwright, BrowserContext, Page

# ── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("base_url", nargs="?", default="https://nodeposit.kubetest.uk")
parser.add_argument("--property-id", type=int, default=None)
args = parser.parse_args()

BASE        = args.base_url.rstrip("/")
PROPERTY_ID = args.property_id

# ── Colours ──────────────────────────────────────────────────────────────────
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"
SKIP = "\033[90m[SKIP]\033[0m"
HEAD = "\033[93m━━━━\033[0m"

results: list[dict] = []


def log_pass(name: str, detail: str = "") -> None:
    print(f"  {PASS} {name}" + (f"  ({detail})" if detail else ""))
    results.append({"name": name, "ok": True})


def log_fail(name: str, detail: str = "") -> None:
    print(f"  {FAIL} {name}" + (f"  → {detail}" if detail else ""))
    results.append({"name": name, "ok": False})


def log_skip(name: str, reason: str = "") -> None:
    print(f"  {SKIP} {name}" + (f"  [{reason}]" if reason else ""))


def section(title: str) -> None:
    print(f"\n{HEAD} {title}")


# ── OIDC login ───────────────────────────────────────────────────────────────
async def login(context: BrowserContext, username: str, password: str) -> Page:
    """Complete the OIDC flow and return the authenticated page."""
    page = await context.new_page()
    await page.goto(f"{BASE}/", wait_until="networkidle", timeout=20_000)

    if "openid-connect/auth" not in page.url and "auth/realms" not in page.url:
        raise RuntimeError(f"Expected Keycloak redirect, landed on: {page.url}")

    await page.wait_for_selector("#username", timeout=10_000)
    await page.fill("#username", username)
    await page.fill("#password", password)
    async with page.expect_navigation(wait_until="networkidle", timeout=20_000):
        await page.click("#kc-login")

    if "auth.kubetest.uk" in page.url:
        try:
            err = await page.inner_text(".alert-error", timeout=2_000)
            raise RuntimeError(f"Keycloak login failed: {err.strip()}")
        except Exception:
            raise RuntimeError(f"Still on Keycloak after submit: {page.url}")

    return page


# ── API helper ────────────────────────────────────────────────────────────────
async def api(page: Page, method: str, path: str, body: dict | None = None) -> tuple[int, any]:
    """Make an authenticated API request using the page's session cookies."""
    url = f"{BASE}{path}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    kwargs: dict = {"headers": headers}
    if body is not None:
        kwargs["data"] = json.dumps(body)

    resp = await getattr(page.request, method.lower())(url, **kwargs)
    try:
        data = await resp.json()
    except Exception:
        data = None
    return resp.status, data


async def check(
    page: Page,
    name: str,
    method: str,
    path: str,
    expected: int,
    body: dict | None = None,
    validate=None,
) -> any:
    """Make an API call, assert the status, optionally validate the body."""
    status, data = await api(page, method, path, body)
    if status != expected:
        log_fail(name, f"expected {expected}, got {status}")
        return data
    if validate is not None:
        err = validate(data)
        if err:
            log_fail(name, err)
            return data
    log_pass(name)
    return data


# ── Validators ────────────────────────────────────────────────────────────────
def is_list(d):
    if not isinstance(d, list):
        return "response is not a list"


def has_role(expected: str):
    def _check(d):
        got = d.get("role") if isinstance(d, dict) else None
        if got != expected:
            return f"expected role={expected!r}, got {got!r}"
    return _check


def has_keys(*keys):
    def _check(d):
        if not isinstance(d, dict):
            return "response is not a dict"
        missing = [k for k in keys if k not in d]
        if missing:
            return f"missing keys: {missing}"
    return _check


# ── Test suites ───────────────────────────────────────────────────────────────
async def suite_tenant(page: Page) -> dict:
    """Returns ctx dict with application_id if CRUD flow ran."""
    ctx: dict = {}

    # ── Read endpoints ────────────────────────────────────────────────────
    await check(page, "GET /api/v1/users/me/ returns role=tenant",
                "GET", "/api/v1/users/me/", 200, validate=has_role("tenant"))

    await check(page, "GET /api/v1/applications/ returns a list",
                "GET", "/api/v1/applications/", 200, validate=is_list)

    await check(page, "GET /api/v1/guarantees/ returns a list",
                "GET", "/api/v1/guarantees/", 200, validate=is_list)

    await check(page, "GET /api/v1/users/me/export/ has profile + applications keys",
                "GET", "/api/v1/users/me/export/", 200,
                validate=has_keys("profile", "applications", "guarantees"))

    # ── Role rejections ───────────────────────────────────────────────────
    await check(page, "POST /api/v1/guarantees/ → 403 (agent-only)",
                "POST", "/api/v1/guarantees/", 403,
                body={"application": 9999, "valid_until": "2027-01-01"})

    await check(page, "POST /api/v1/claims/ → 403 (landlord-only)",
                "POST", "/api/v1/claims/", 403,
                body={"guarantee": 9999, "amount_claimed": "100.00"})

    # ── CRUD: submit application ──────────────────────────────────────────
    if not PROPERTY_ID:
        log_skip("POST /api/v1/applications/", "no --property-id given")
        return ctx

    section("Tenant: submit application")
    status, data = await api(page, "POST", "/api/v1/applications/",
                             body={"property": PROPERTY_ID})
    if status == 201 and isinstance(data, dict):
        log_pass("POST /api/v1/applications/ → 201", f"id={data.get('id')}")
        ctx["application_id"] = data["id"]
    elif status == 400:
        # Already applied — find the existing one
        log_pass("POST /api/v1/applications/ → 400 (already applied)", str(data))
        _, apps = await api(page, "GET", "/api/v1/applications/")
        existing = next((a for a in (apps or []) if a.get("property") == PROPERTY_ID), None)
        if existing:
            ctx["application_id"] = existing["id"]
            print(f"      Reusing application id={existing['id']}")
    else:
        log_fail("POST /api/v1/applications/ → 201", f"got {status}: {data}")

    return ctx


async def suite_landlord(page: Page, guarantee_id: int | None) -> None:
    # ── Read endpoints ────────────────────────────────────────────────────
    await check(page, "GET /api/v1/users/me/ returns role=landlord",
                "GET", "/api/v1/users/me/", 200, validate=has_role("landlord"))

    await check(page, "GET /api/v1/applications/ returns a list",
                "GET", "/api/v1/applications/", 200, validate=is_list)

    await check(page, "GET /api/v1/claims/ returns a list",
                "GET", "/api/v1/claims/", 200, validate=is_list)

    await check(page, "GET /api/v1/users/me/export/ succeeds",
                "GET", "/api/v1/users/me/export/", 200, validate=has_keys("profile"))

    # ── Role rejection ────────────────────────────────────────────────────
    await check(page, "POST /api/v1/guarantees/ → 403 (agent-only)",
                "POST", "/api/v1/guarantees/", 403,
                body={"application": 9999, "valid_until": "2027-01-01"})

    # ── CRUD: submit claim ────────────────────────────────────────────────
    if not guarantee_id:
        log_skip("POST /api/v1/claims/", "no guarantee from agent step")
        return

    section("Landlord: submit damage claim")
    status, data = await api(page, "POST", "/api/v1/claims/",
                              body={"guarantee": guarantee_id,
                                    "amount_claimed": "500.00",
                                    "evidence_urls": [],
                                    "notes": "e2e-test claim"})
    if status == 201:
        log_pass("POST /api/v1/claims/ → 201", f"id={data.get('id') if data else '?'}")
    elif status == 400:
        log_pass("POST /api/v1/claims/ → 400 (already submitted)", str(data))
    else:
        log_fail("POST /api/v1/claims/ → 201", f"got {status}: {data}")


async def suite_agent(page: Page, application_id: int | None) -> dict:
    ctx: dict = {}

    # ── Read endpoints ────────────────────────────────────────────────────
    await check(page, "GET /api/v1/users/me/ returns role=agent",
                "GET", "/api/v1/users/me/", 200, validate=has_role("agent"))

    await check(page, "GET /api/v1/applications/ returns a list",
                "GET", "/api/v1/applications/", 200, validate=is_list)

    await check(page, "GET /api/v1/guarantees/ returns a list",
                "GET", "/api/v1/guarantees/", 200, validate=is_list)

    await check(page, "GET /api/v1/claims/ returns a list",
                "GET", "/api/v1/claims/", 200, validate=is_list)

    # ── CRUD: review application ──────────────────────────────────────────
    if not application_id:
        log_skip("PATCH /api/v1/applications/{id}/review/", "no application_id from tenant step")
        return ctx

    section("Agent: review application")
    status, data = await api(page, "PATCH",
                             f"/api/v1/applications/{application_id}/review/",
                             body={"decision": "approved", "notes": "e2e-test"})
    if status == 200:
        log_pass(f"PATCH /api/v1/applications/{application_id}/review/ → 200 (approved)")
    elif status == 400 and "pending" in str(data).lower():
        log_pass(f"PATCH review → 400 (already reviewed)", str(data))
    else:
        log_fail(f"PATCH /api/v1/applications/{application_id}/review/ → 200",
                 f"got {status}: {data}")

    # ── CRUD: issue guarantee ─────────────────────────────────────────────
    section("Agent: issue guarantee")
    status, data = await api(page, "POST", "/api/v1/guarantees/",
                              body={"application": application_id, "valid_until": "2027-12-31"})
    if status == 201 and isinstance(data, dict):
        log_pass("POST /api/v1/guarantees/ → 201",
                 f"cert={data.get('certificate_number')}")
        ctx["guarantee_id"] = data["id"]
    elif status == 400 and "already exists" in str(data).lower():
        log_pass("POST /api/v1/guarantees/ → 400 (already issued)", str(data))
        _, guarantees = await api(page, "GET", "/api/v1/guarantees/")
        existing = next(
            (g for g in (guarantees or []) if g.get("application") == application_id), None
        )
        if existing:
            ctx["guarantee_id"] = existing["id"]
            print(f"      Reusing guarantee id={existing['id']}")
    else:
        log_fail("POST /api/v1/guarantees/ → 201", f"got {status}: {data}")

    # ── Validate endpoint ─────────────────────────────────────────────────
    if ctx.get("guarantee_id"):
        await check(page,
                    f"GET /api/v1/guarantees/{ctx['guarantee_id']}/validate/ → 200",
                    "GET", f"/api/v1/guarantees/{ctx['guarantee_id']}/validate/", 200,
                    validate=has_keys("certificate_number", "status", "valid_until"))

    return ctx


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    print(f"\n{INFO} No-Deposit E2E API Test Suite")
    print(f"{INFO} Target: {BASE}")
    if PROPERTY_ID:
        print(f"{INFO} CRUD flow: enabled (--property-id {PROPERTY_ID})")
    else:
        print(f"{INFO} CRUD flow: disabled (pass --property-id N to enable)")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ── Tenant ────────────────────────────────────────────────────────
        section("Login: tenant1")
        try:
            tenant_page = await login(await browser.new_context(), "tenant1", "Tenant1Pass!")
            log_pass("tenant1 OIDC login")
        except Exception as e:
            log_fail("tenant1 OIDC login", str(e))
            _summary()
            sys.exit(1)

        section("Tenant endpoint checks")
        tenant_ctx = await suite_tenant(tenant_page)

        # ── Agent ─────────────────────────────────────────────────────────
        section("Login: agent1")
        try:
            agent_page = await login(await browser.new_context(), "agent1", "Agent1Pass!")
            log_pass("agent1 OIDC login")
            section("Agent endpoint checks")
            agent_ctx = await suite_agent(agent_page, tenant_ctx.get("application_id"))
        except Exception as e:
            log_fail("agent1 OIDC login", str(e))
            agent_ctx = {}

        # ── Landlord ─────────────────────────────────────────────────────
        section("Login: landlord1")
        try:
            landlord_page = await login(await browser.new_context(), "landlord1", "Landlord1Pass!")
            log_pass("landlord1 OIDC login")
            section("Landlord endpoint checks")
            await suite_landlord(landlord_page, agent_ctx.get("guarantee_id"))
        except Exception as e:
            log_fail("landlord1 OIDC login", str(e))

        await browser.close()

    _summary()
    sys.exit(1 if any(not r["ok"] for r in results) else 0)


def _summary() -> None:
    total  = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed
    print(f"\n{'━'*52}")
    print(f"  {passed}/{total} passed", end="")
    if failed:
        print(f"   {failed} FAILED:")
        for r in results:
            if not r["ok"]:
                print(f"    {FAIL} {r['name']}")
    else:
        print("  ✓ all green")
    print(f"{'━'*52}\n")


if __name__ == "__main__":
    asyncio.run(main())
