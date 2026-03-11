"""
Frontend capability sanity checks
Verifies that each major UI route loads successfully with backend services running.
"""

import requests
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime

BASE_URL = "http://localhost:3000"
TIMEOUT = 10


@dataclass
class CapabilityCheck:
    name: str
    path: str
    keywords: List[str] = field(default_factory=list)
    requires_auth: bool = False


CAPABILITIES: List[CapabilityCheck] = [
    CapabilityCheck(
        name="Landing",
        path="/",
        keywords=["AI Trading", "Screener"]
    ),
    CapabilityCheck(
        name="Authentication",
        path="/auth/login",
        keywords=["Sign in", "Email"]
    ),
    CapabilityCheck(
        name="Dashboard",
        path="/dashboard",
        keywords=["Dashboard", "Screener"]
    ),
    CapabilityCheck(
        name="Predictions",
        path="/predictions",
        keywords=["Predictions", "Backtest"]
    ),
    CapabilityCheck(
        name="Screener",
        path="/screener",
        keywords=["Screener", "Filters"]
    ),
    CapabilityCheck(
        name="Watchlist",
        path="/watchlist",
        keywords=["Watchlist"]
    ),
    CapabilityCheck(
        name="Portfolio",
        path="/portfolio",
        keywords=["Portfolio", "Total Value"]
    ),
    CapabilityCheck(
        name="Paper Trading",
        path="/paper-trading",
        keywords=["Paper Trading", "Account"]
    ),
    CapabilityCheck(
        name="Analytics",
        path="/analytics",
        keywords=["Analytics", "Performance"]
    ),
    CapabilityCheck(
        name="Subscriptions",
        path="/subscription",
        keywords=["Subscription", "Plan"]
    ),
    CapabilityCheck(
        name="Referrals",
        path="/referrals",
        keywords=["Referral"]
    ),
    CapabilityCheck(
        name="News & Sentiment",
        path="/news",
        keywords=["News", "Sentiment"]
    ),
]


def check_capability(cap: CapabilityCheck) -> Dict:
    """Return status dict for a capability path."""
    url = f"{BASE_URL}{cap.path}"
    result = {
        "capability": cap.name,
        "url": url,
        "status": "fail",
        "http_status": None,
        "details": ""
    }
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        result["http_status"] = resp.status_code
        if resp.status_code != 200:
            result["details"] = f"Unexpected status {resp.status_code}"
            return result
        body = resp.text
        missing = [k for k in cap.keywords if k and k not in body]
        if missing:
            result["status"] = "warn"
            result["details"] = f"Missing keywords: {', '.join(missing)}"
        else:
            result["status"] = "pass"
            result["details"] = "Page loaded with expected content"
    except Exception as exc:
        result["details"] = f"Error: {exc}"
    return result


def run():
    print("=" * 80)
    print("Frontend Capability Sanity Report")
    print(f"Started: {datetime.now().isoformat(timespec='seconds')}")
    print("=" * 80)

    summary = {"pass": 0, "warn": 0, "fail": 0}
    results = []

    for cap in CAPABILITIES:
        res = check_capability(cap)
        summary[res["status"]] += 1
        results.append(res)
        status = res["status"].upper()
        http = res["http_status"]
        details = res["details"]
        print(f"[{status}] {cap.name} ({cap.path}) -> HTTP {http} | {details}")

    print("\n" + "-" * 80)
    print("Summary")
    print("-" * 80)
    total = len(CAPABILITIES)
    print(f"Total capabilities: {total}")
    for key in ["pass", "warn", "fail"]:
        print(f"{key.title()}: {summary[key]}")

    cert = "PASS" if summary["fail"] == 0 else "PARTIAL"
    print(f"\nCertification: {cert}")
    print("=" * 80)

    return results, summary


if __name__ == "__main__":
    run()



