from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests


def ensure_route(routes: list[dict[str, Any]], model_id: str, provider: str, account_id: str) -> list[dict[str, Any]]:
    route = next((route for route in routes if route.get("modelId") == model_id), None)
    entry = {
        "id": f"agentic-{model_id}-{provider}",
        "provider": provider,
        "accountId": account_id,
        "label": f"{provider}:{model_id}",
        "accountLabel": account_id,
    }
    if route is None:
        routes.append(
            {
                "id": f"agentic-{model_id}",
                "modelId": model_id,
                "entries": [entry],
            }
        )
        return routes

    route["entries"] = [existing for existing in route.get("entries", []) if existing.get("provider") != provider]
    route["entries"].insert(0, entry)
    return routes


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Anti-API account routing for the agentic app.")
    parser.add_argument("--anti-api-url", default="http://localhost:8964", help="Base URL for Anti-API.")
    args = parser.parse_args()

    base_url = args.anti_api_url.rstrip("/")
    accounts_response = requests.get(f"{base_url}/auth/accounts", timeout=30)
    accounts_response.raise_for_status()
    accounts = accounts_response.json()["accounts"]

    codex_accounts = accounts.get("codex") or []
    antigravity_accounts = accounts.get("antigravity") or []
    if not codex_accounts:
        raise RuntimeError("No Codex account found in Anti-API. gpt-5.4 routing cannot be configured.")
    if not antigravity_accounts:
        raise RuntimeError("No Antigravity account found in Anti-API. claude-opus-4-6 planning cannot be configured.")

    config_response = requests.get(f"{base_url}/routing/config", timeout=30)
    config_response.raise_for_status()
    payload = config_response.json()
    config = payload.get("config", {})
    account_routing = config.get("accountRouting") or {"smartSwitch": False, "routes": []}
    routes = list(account_routing.get("routes") or [])

    routes = ensure_route(routes, "gpt-5.4", "codex", codex_accounts[0]["id"])
    routes = ensure_route(routes, "claude-opus-4-6-thinking", "antigravity", antigravity_accounts[0]["id"])

    update_payload = {
        "accountRouting": {
            "smartSwitch": account_routing.get("smartSwitch", False),
            "routes": routes,
        }
    }
    update_response = requests.post(f"{base_url}/routing/config", json=update_payload, timeout=30)
    update_response.raise_for_status()
    print(json.dumps(update_response.json(), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"bootstrap_antiapi_routing failed: {exc}", file=sys.stderr)
        sys.exit(1)
