#!/usr/bin/env python3
"""
Seed test data for the no-deposit e2e test cycle.

Logs in as landlord1 via OIDC, then ensures the sentinel test property
exists. Prints the property ID on the last line so the CI workflow can
capture it:

    PROPERTY_ID=$(python scripts/seed-e2e.py https://nodeposit.kubetest.uk)

Pass --reset to delete the previous cycle's applications/guarantees/claims
via the API so the full CRUD flow can run again from scratch.

Usage:
    python scripts/seed-e2e.py [BASE_URL] [--reset]
"""

import asyncio
import argparse
import json
import sys

from playwright.async_api import async_playwright

SENTINEL_ADDRESS = "E2E Test Property, 1 Demo Street, London E1 1AA"

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("base_url", nargs="?", default="https://nodeposit.kubetest.uk")
parser.add_argument(
    "--reset",
    action="store_true",
    help="Delete previous cycle's applications/guarantees/claims first",
)
args = parser.parse_args()

BASE = args.base_url.rstrip("/")

INFO = "\033[94m[INFO]\033[0m"
OK = "\033[92m[ OK ]\033[0m"
WARN = "\033[93m[WARN]\033[0m"
ERR = "\033[91m[ERR ]\033[0m"


async def login(browser, username: str, password: str):
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(f"{BASE}/", wait_until="networkidle", timeout=20_000)
    if "openid-connect/auth" not in page.url and "auth/realms" not in page.url:
        print(
            f"{ERR} Expected Keycloak redirect, landed on: {page.url}", file=sys.stderr
        )
        sys.exit(1)
    await page.wait_for_selector("#username", timeout=10_000)
    await page.fill("#username", username)
    await page.fill("#password", password)
    async with page.expect_navigation(wait_until="networkidle", timeout=20_000):
        await page.click("#kc-login")
    if "auth.kubetest.uk" in page.url:
        print(f"{ERR} Login failed — still on Keycloak: {page.url}", file=sys.stderr)
        sys.exit(1)
    print(f"{OK} Logged in as {username}", file=sys.stderr)
    return page


async def api(page, method: str, path: str, body=None):
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


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ── Log in as landlord1 ───────────────────────────────────────────────
        page = await login(browser, "landlord1", "Landlord1Pass!")

        # ── Find or create the sentinel property ─────────────────────────────
        status_code, props = await api(page, "GET", "/api/v1/properties/")
        if status_code != 200:
            print(
                f"{ERR} GET /api/v1/properties/ returned {status_code}: {props}",
                file=sys.stderr,
            )
            sys.exit(1)

        existing = next(
            (p for p in (props or []) if p.get("address") == SENTINEL_ADDRESS), None
        )

        if existing:
            prop_id = existing["id"]
            print(
                f"{INFO} Test property already exists (id={prop_id})", file=sys.stderr
            )

            if args.reset:
                await reset_cycle(prop_id)
        else:
            status_code, data = await api(
                page,
                "POST",
                "/api/v1/properties/",
                body={
                    "address": SENTINEL_ADDRESS,
                    "rent_amount": "1200.00",
                    "status": "available",
                },
            )
            if status_code != 201 or not isinstance(data, dict):
                print(
                    f"{ERR} POST /api/v1/properties/ returned {status_code}: {data}",
                    file=sys.stderr,
                )
                sys.exit(1)
            prop_id = data["id"]
            print(f"{OK} Created test property (id={prop_id})", file=sys.stderr)

        await browser.close()

    # Machine-parseable: just the ID on stdout
    print(prop_id)


async def reset_cycle(prop_id: int):
    """
    Delete all applications/guarantees/claims for the test property so the
    CRUD flow can run from scratch. Uses the agent1 session to access all records.
    """
    print(
        f"{INFO} --reset: removing previous cycle data for property {prop_id}...",
        file=sys.stderr,
    )

    # Re-login as agent to see all applications
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        agent_page = await login(browser, "agent1", "Agent1Pass!")

        _, apps = await api(agent_page, "GET", "/api/v1/applications/")
        target_apps = [a for a in (apps or []) if a.get("property") == prop_id]

        _, guarantees = await api(agent_page, "GET", "/api/v1/guarantees/")
        target_guarantee_ids = {
            g["id"]
            for g in (guarantees or [])
            if g.get("application") in {a["id"] for a in target_apps}
        }

        _, claims = await api(agent_page, "GET", "/api/v1/claims/")
        target_claims = [
            c for c in (claims or []) if c.get("guarantee") in target_guarantee_ids
        ]

        await browser.close()

    print(
        f"{INFO}   Found: {len(target_claims)} claim(s), "
        f"{len(target_guarantee_ids)} guarantee(s), "
        f"{len(target_apps)} application(s)",
        file=sys.stderr,
    )
    print(
        f"{WARN}   API has no DELETE endpoints — use the management command to reset:\n"
        f"        python manage.py seed_e2e --reset\n"
        f"   Or run the kubectl one-off pod (see docs/DEBUGGING_RULESET.md for the pattern)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    asyncio.run(main())
