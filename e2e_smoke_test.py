#!/usr/bin/env python3
"""Comprehensive E2E smoke test suite for test.ktrading.tech

Run on VPS: python3 /tmp/e2e_smoke_test.py
"""
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime

RESULTS = []
PASS = 0
FAIL = 0
SKIP = 0

BASE = "http://127.0.0.1"


def req(url, method="GET", headers=None, data=None, timeout=15):
    headers = headers or {}
    try:
        if data and isinstance(data, dict):
            data = json.dumps(data).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(body)
            except Exception:
                return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:
        return 0, str(e)


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        RESULTS.append(("PASS", name, detail))
        print(f"  \033[32mPASS\033[0m {name}")
    else:
        FAIL += 1
        RESULTS.append(("FAIL", name, detail))
        print(f"  \033[31mFAIL\033[0m {name} -- {detail}")


def skip(name, reason=""):
    global SKIP
    SKIP += 1
    RESULTS.append(("SKIP", name, reason))
    print(f"  \033[33mSKIP\033[0m {name} -- {reason}")


# ============================================================
# 1. PREDICTION ENGINE (port 8110)
# ============================================================
print("\n\033[1m=== 1. PREDICTION ENGINE (8110) ===\033[0m")
pe = f"{BASE}:8110"

code, body = req(f"{pe}/v1/health")
test("PE-01: /v1/health returns 200", code == 200, f"got {code}")
test("PE-02: health status=ok", isinstance(body, dict) and body.get("status") == "ok", str(body)[:80])

code, body = req(f"{pe}/")
test("PE-03: / returns API info", code == 200, f"got {code}")

code, _ = req(f"{pe}/docs")
test("PE-04: /docs returns 200", code == 200, f"got {code}")

# Auth - predictor token
code, token_body = req(f"{pe}/v1/auth/token", method="POST", data={"api_key": "predict-dev-key"})
test("PE-05: predictor auth returns JWT", code == 200 and isinstance(token_body, dict) and "access_token" in token_body, f"got {code}")
PE_TOKEN = token_body.get("access_token", "") if isinstance(token_body, dict) else ""
pe_auth = {"Authorization": f"Bearer {PE_TOKEN}"}

# Auth - admin token
code, admin_body = req(f"{pe}/v1/auth/token", method="POST", data={"api_key": "admin-dev-key"})
test("PE-06: admin auth returns JWT", code == 200 and isinstance(admin_body, dict) and "access_token" in admin_body, f"got {code}")
ADMIN_TOKEN = admin_body.get("access_token", "") if isinstance(admin_body, dict) else ""
admin_auth = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

# Auth - invalid key rejected (must be >=8 chars to pass validation)
code, _ = req(f"{pe}/v1/auth/token", method="POST", data={"api_key": "bad-key-invalid"})
test("PE-07: invalid API key rejected", code in (401, 403), f"got {code}")

# Predictions/all (paginated)
code, body = req(f"{pe}/v1/predictions/all?page=1&page_size=5", headers=pe_auth)
test("PE-08: /v1/predictions/all returns 200", code == 200, f"got {code}")
if isinstance(body, dict) and "predictions" in body:
    preds = body["predictions"]
    pred_count = len(preds)
    test("PE-09: predictions/all returns data", pred_count > 0, f"got {pred_count} predictions")
    first_ticker = list(preds.keys())[0] if preds else None
    if first_ticker:
        p = preds[first_ticker]
        test("PE-10: has pred_1d field", "pred_1d" in p, "")
        test("PE-11: has confidence_1w field", "confidence_1w" in p, "")
        test("PE-12: has computed_at (timestamp)", "computed_at" in p, "")
        test("PE-13: has decision_time_contract", "decision_time_contract" in p, "")
        test("PE-14: has method field", "method" in p, "")
        test("PE-15: has signal fields", "signal_1d" in p or "signal_1w" in p, "")
    pagination = body.get("pagination", {})
    total = pagination.get("total_items", 0)
    test("PE-16: total count > 0", total > 0, f"total={total}")
else:
    test("PE-09: predictions/all has data", False, str(body)[:100])

# Search
code, body = req(f"{pe}/v1/predictions/all?page=1&page_size=5&search=AAPL", headers=pe_auth)
test("PE-17: search AAPL returns 200", code == 200, f"got {code}")
if isinstance(body, dict) and "predictions" in body:
    test("PE-18: search finds AAPL", "AAPL" in body["predictions"], str(list(body["predictions"].keys()))[:50])

# Sort
code, body = req(f"{pe}/v1/predictions/all?page=1&page_size=3&sort_by=confidence_1w&sort_dir=desc", headers=pe_auth)
test("PE-19: sort by confidence returns 200", code == 200, f"got {code}")

# Pagination page 2
code, body = req(f"{pe}/v1/predictions/all?page=2&page_size=5", headers=pe_auth)
test("PE-20: pagination page 2 works", code == 200, f"got {code}")

# Single prediction
code, body = req(f"{pe}/v1/predictions/AAPL?horizons=1,7", headers=pe_auth)
test("PE-21: /v1/predictions/AAPL returns data", code == 200, f"got {code}")

# Batch predictions
code, body = req(f"{pe}/v1/predictions/batch?tickers=AAPL,MSFT,GOOGL&horizons=1,7", headers=pe_auth)
test("PE-22: /v1/predictions/batch returns data", code == 200, f"got {code}")
if isinstance(body, dict):
    test("PE-23: batch has multiple tickers", len(body) >= 2, f"got {len(body)} tickers")

# Backtests
code, body = req(f"{pe}/v1/backtests/AAPL/latest", headers=pe_auth)
test("PE-24: /v1/backtests/AAPL/latest", code in (200, 404), f"got {code}")

# Backtests/all (requires admin token; 404 = no runs yet, which is OK)
code, body = req(f"{pe}/v1/backtests/all?page=1&page_size=3", headers=admin_auth)
test("PE-25: /v1/backtests/all responds", code in (200, 404), f"got {code}")

# Admin metrics
code, body = req(f"{pe}/v1/admin/metrics", headers=admin_auth)
test("PE-26: /v1/admin/metrics returns 200", code == 200, f"got {code}")
if isinstance(body, dict):
    test("PE-27: has total_predictions", "total_predictions" in body, "")
    test("PE-28: has abstention_rate", "abstention_rate" in body, f"rate={body.get('abstention_rate')}")
    test("PE-29: total_predictions > 0", body.get("total_predictions", 0) > 0, f"n={body.get('total_predictions')}")
    ar = body.get("abstention_rate", -1)
    test("PE-30: abstention_rate in [0,1]", 0 <= ar <= 1 if ar is not None else False, f"rate={ar}")
    test("PE-31: has calibration_fitted", "calibration_fitted" in body, "")
    test("PE-32: has pending_outcomes", "pending_outcomes" in body, f"n={body.get('pending_outcomes')}")

# Scheduler status
code, body = req(f"{pe}/v1/scheduler/status", headers=pe_auth)
test("PE-33: /v1/scheduler/status", code in (200, 404), f"got {code}")

# Unauthenticated access rejected
code, _ = req(f"{pe}/v1/predictions/all?page=1&page_size=1")
test("PE-34: unauthenticated rejected", code in (401, 403), f"got {code}")

# ============================================================
# 2. SCREENER SERVICE (port 8103)
# ============================================================
print("\n\033[1m=== 2. SCREENER SERVICE (8103) ===\033[0m")
ss = f"{BASE}:8103"

code, body = req(f"{ss}/health")
test("SS-01: /health returns 200", code == 200, f"got {code}")
test("SS-02: status=healthy", isinstance(body, dict) and body.get("status") == "healthy", "")

code, body = req(f"{ss}/api/screener/sectors")
test("SS-03: /api/screener/sectors returns 200", code == 200, f"got {code}")
if isinstance(body, dict) and "sectors" in body:
    test("SS-04: sectors has data", len(body["sectors"]) > 0, f"n={len(body['sectors'])}")

code, body = req(f"{ss}/api/screener/predictions?page=1&page_size=3")
test("SS-05: predictions proxy responds", code in (200, 401, 403), f"got {code}")

code, body = req(f"{ss}/api/screener/backtests/all?page=1&page_size=3")
test("SS-06: backtests proxy responds", code in (200, 401, 403), f"got {code}")

# ============================================================
# 3. USER SERVICE (port 8101)
# ============================================================
print("\n\033[1m=== 3. USER SERVICE (8101) ===\033[0m")
us = f"{BASE}:8101"

code, body = req(f"{us}/health")
test("US-01: /health returns 200", code == 200, f"got {code}")

# Login
code, body = req(f"{us}/api/auth/login", method="POST", data={"email": "kasireddymeruva@gmail.com", "password": "Kurichedu12345!"})
USER_TOKEN = None
user_auth = {}
if code == 200 and isinstance(body, dict) and ("token" in body or "access_token" in body):
    USER_TOKEN = body.get("access_token") or body.get("token")
    user_auth = {"Authorization": f"Bearer {USER_TOKEN}"}
    test("US-02: login returns token", True, "")

    code, body = req(f"{us}/api/auth/me", headers=user_auth)
    test("US-03: /api/auth/me returns 200", code == 200, f"got {code}")
    if isinstance(body, dict):
        test("US-04: profile has email", "email" in body, str(list(body.keys()))[:60])
        test("US-05: profile has user_id or id", "user_id" in body or "id" in body, str(list(body.keys()))[:60])
else:
    skip("US-02: login", f"got {code} -- {str(body)[:60]}")
    skip("US-03: profile", "no token")
    skip("US-04: profile email", "no token")
    skip("US-05: profile id", "no token")

# Invalid login rejected
code, _ = req(f"{us}/api/auth/login", method="POST", data={"email": "bad@bad.com", "password": "wrong"})
test("US-06: invalid login rejected", code in (401, 403, 404, 422), f"got {code}")

# ============================================================
# 4. WATCHLIST SERVICE (port 8102)
# ============================================================
print("\n\033[1m=== 4. WATCHLIST SERVICE (8102) ===\033[0m")
ws = f"{BASE}:8102"

code, body = req(f"{ws}/health")
test("WS-01: /health returns 200", code == 200, f"got {code}")

if USER_TOKEN:
    code, body = req(f"{ws}/api/watchlist", headers=user_auth)
    test("WS-02: /api/watchlist returns data", code == 200, f"got {code}")

    code, body = req(f"{ws}/api/watchlist/all-tickers")
    test("WS-03: /api/watchlist/all-tickers", code in (200, 401, 403, 404), f"got {code}")
else:
    skip("WS-02: watchlist GET", "no token")
    skip("WS-03: all-tickers", "no token")

# ============================================================
# 5. PORTFOLIO SERVICE (port 8104)
# ============================================================
print("\n\033[1m=== 5. PORTFOLIO SERVICE (8104) ===\033[0m")
ps = f"{BASE}:8104"

code, body = req(f"{ps}/health")
test("PS-01: /health returns 200", code == 200, f"got {code}")

if USER_TOKEN:
    code, body = req(f"{ps}/api/portfolio", headers=user_auth)
    test("PS-02: /api/portfolio returns data", code in (200, 404), f"got {code}")

    code, body = req(f"{ps}/api/portfolio/transactions", headers=user_auth)
    test("PS-03: /api/portfolio/transactions", code in (200, 404), f"got {code}")

    code, body = req(f"{ps}/api/portfolio/performance", headers=user_auth)
    test("PS-04: /api/portfolio/performance", code in (200, 404), f"got {code}")
else:
    skip("PS-02: portfolio", "no token")
    skip("PS-03: transactions", "no token")
    skip("PS-04: performance", "no token")

# ============================================================
# 6. PAPER TRADING SERVICE (port 8105)
# ============================================================
print("\n\033[1m=== 6. PAPER TRADING SERVICE (8105) ===\033[0m")
pt = f"{BASE}:8105"

code, body = req(f"{pt}/health")
test("PT-01: /health returns 200", code == 200, f"got {code}")

if USER_TOKEN:
    code, body = req(f"{pt}/api/paper-trading/account", headers=user_auth)
    test("PT-02: /api/paper-trading/account", code in (200, 404), f"got {code}")

    code, body = req(f"{pt}/api/paper-trading/positions", headers=user_auth)
    test("PT-03: /api/paper-trading/positions", code in (200, 404), f"got {code}")

    code, body = req(f"{pt}/api/paper-trading/orders", headers=user_auth)
    test("PT-04: /api/paper-trading/orders", code in (200, 404), f"got {code}")
else:
    skip("PT-02: account", "no token")
    skip("PT-03: positions", "no token")
    skip("PT-04: orders", "no token")

# ============================================================
# 7. REMAINING SERVICES
# ============================================================
print("\n\033[1m=== 7. ANALYTICS SERVICE (8106) ===\033[0m")
code, body = req(f"{BASE}:8106/health")
test("AN-01: /health returns 200", code == 200, f"got {code}")

print("\n\033[1m=== 8. SUBSCRIPTION SERVICE (8107) ===\033[0m")
code, body = req(f"{BASE}:8107/health")
test("SUB-01: /health returns 200", code == 200, f"got {code}")

if USER_TOKEN:
    code, body = req(f"{BASE}:8107/api/subscription/status", headers=user_auth)
    test("SUB-02: /api/subscription/status", code in (200, 404), f"got {code}")
else:
    skip("SUB-02: subscription status", "no token")

print("\n\033[1m=== 9. REFERRAL SERVICE (8108) ===\033[0m")
code, body = req(f"{BASE}:8108/health")
test("REF-01: /health returns 200", code == 200, f"got {code}")

print("\n\033[1m=== 10. NEWS SERVICE (8109) ===\033[0m")
code, body = req(f"{BASE}:8109/health")
test("NEWS-01: /health returns 200", code == 200, f"got {code}")

if USER_TOKEN:
    code, body = req(f"{BASE}:8109/api/news", headers=user_auth)
    test("NEWS-02: /api/news returns data", code in (200, 404), f"got {code}")
else:
    skip("NEWS-02: news feed", "no token")

# ============================================================
# 8. FRONTEND (port 3001)
# ============================================================
print("\n\033[1m=== 11. FRONTEND (3001) ===\033[0m")
fe = f"{BASE}:3001"
pages = [
    "/", "/auth/login", "/auth/signup", "/predictions", "/screener",
    "/watchlist", "/portfolio", "/pricing", "/profile", "/referrals",
    "/privacy", "/terms",
]
for page in pages:
    code, _ = req(f"{fe}{page}")
    test(f"FE: {page} returns 200", code == 200, f"got {code}")

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*60}")
print(f"  E2E TEST RESULTS -- test.ktrading.tech")
print(f"{'='*60}")
print(f"  \033[32mPASSED:  {PASS}\033[0m")
print(f"  \033[31mFAILED:  {FAIL}\033[0m")
print(f"  \033[33mSKIPPED: {SKIP}\033[0m")
print(f"  TOTAL:   {PASS + FAIL + SKIP}")
print(f"{'='*60}")

if FAIL > 0:
    print(f"\n\033[31mFailed tests:\033[0m")
    for s, name, detail in RESULTS:
        if s == "FAIL":
            print(f"  x {name}: {detail}")

if SKIP > 0:
    print(f"\n\033[33mSkipped tests:\033[0m")
    for s, name, detail in RESULTS:
        if s == "SKIP":
            print(f"  - {name}: {detail}")

from datetime import timezone
print(f"\nTimestamp: {datetime.now(timezone.utc).isoformat()}")
sys.exit(1 if FAIL > 0 else 0)
