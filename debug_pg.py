#!/usr/bin/env python3
"""Debug watchlist and paper trading PG data."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1"

def req(url, method="GET", headers=None, data=None):
    headers = headers or {}
    try:
        if data and isinstance(data, dict):
            data = json.dumps(data).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=15) as resp:
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

# Get user token
code, body = req(f"{BASE}:8101/api/auth/login", method="POST",
                 data={"email": "kasireddymeruva@gmail.com", "password": "Kurichedu12345!"})
token = body.get("access_token", "") if isinstance(body, dict) else ""
auth = {"Authorization": f"Bearer {token}"}

# Get user profile to find user_id
code, me = req(f"{BASE}:8101/api/auth/me", headers=auth)
print(f"User profile: {json.dumps(me, indent=2)[:300]}")
user_id = me.get("id") or me.get("user_id") if isinstance(me, dict) else "unknown"
print(f"User ID: {user_id}")

# Watchlist raw response
print("\n=== WATCHLIST RAW ===")
code, body = req(f"{BASE}:8102/api/watchlist", headers=auth)
print(f"  type: {type(body).__name__}")
print(f"  code: {code}")
print(f"  body: {json.dumps(body, indent=2)[:500] if isinstance(body, (dict, list)) else str(body)[:500]}")

# Try all-tickers
print("\n=== WATCHLIST ALL-TICKERS ===")
code, body = req(f"{BASE}:8102/api/watchlist/all-tickers")
print(f"  code: {code}, body: {json.dumps(body)[:300] if isinstance(body, (dict, list)) else str(body)[:300]}")

# Paper trading raw response
print("\n=== PAPER TRADING RAW ===")
code, body = req(f"{BASE}:8105/api/paper-trading/account", headers=auth)
print(f"  code: {code}")
print(f"  body: {json.dumps(body, indent=2)[:500] if isinstance(body, (dict, list)) else str(body)[:500]}")

# Try creating a paper account if empty
if isinstance(body, dict) and body.get("cash") is None:
    print("\n  Attempting to place a test order to init account...")
    code2, body2 = req(f"{BASE}:8105/api/paper-trading/orders", method="POST",
                       headers=auth,
                       data={"ticker": "AAPL", "order_type": "market", "side": "buy", "quantity": 1})
    print(f"  order result: code={code2}, body={json.dumps(body2)[:300] if isinstance(body2, (dict, list)) else str(body2)[:300]}")

    # Re-check account
    code3, body3 = req(f"{BASE}:8105/api/paper-trading/account", headers=auth)
    print(f"  account after order: cash={body3.get('cash') if isinstance(body3, dict) else 'N/A'}")
