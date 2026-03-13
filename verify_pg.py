#!/usr/bin/env python3
"""Verify all 3 services are serving data from PostgreSQL correctly."""
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

print("=== STORAGE MODES ===")
for port, name in [(8104, "Portfolio"), (8102, "Watchlist"), (8105, "PaperTrading")]:
    code, body = req(f"{BASE}:{port}/")
    mode = body.get("storage_mode", "unknown") if isinstance(body, dict) else "error"
    print(f"  {name}: {mode}")

print("\n=== PORTFOLIO SERVICE (PG) ===")
code, body = req(f"{BASE}:8104/api/portfolio", headers=auth)
if isinstance(body, dict):
    print(f"  cash: {body.get('cash')}")
    print(f"  positions: {len(body.get('positions', []))}")
    for p in body.get("positions", []):
        print(f"    - {p.get('ticker')}: qty={p.get('quantity')}, avg_cost={p.get('avgCostBasis')}")
    print(f"  totalValue: {body.get('totalValue')}")
else:
    print(f"  ERROR: code={code}, body={str(body)[:200]}")

code, body = req(f"{BASE}:8104/api/portfolio/transactions", headers=auth)
if isinstance(body, dict):
    txns = body.get("transactions", body.get("data", []))
    print(f"  transactions: {len(txns)}")
else:
    print(f"  transactions ERROR: code={code}")

print("\n=== WATCHLIST SERVICE (PG) ===")
code, body = req(f"{BASE}:8102/api/watchlist", headers=auth)
print(f"  code={code}, keys={list(body.keys()) if isinstance(body, dict) else 'not dict'}")
if isinstance(body, dict):
    lists = body.get("lists", body.get("watchlists", []))
    print(f"  lists: {len(lists)}")
    for wl in lists[:3]:
        stocks = wl.get("stocks", [])
        print(f"    - {wl.get('name')}: {len(stocks)} stocks, default={wl.get('isDefault')}")

print("\n=== PAPER TRADING SERVICE (PG) ===")
code, body = req(f"{BASE}:8105/api/paper-trading/account", headers=auth)
if isinstance(body, dict):
    print(f"  cash: {body.get('cash')}")
    print(f"  positions: {len(body.get('positions', []))}")
    for p in body.get("positions", []):
        print(f"    - {p.get('ticker')}: qty={p.get('quantity')}")
    print(f"  total_value: {body.get('totalValue', body.get('total_value'))}")
else:
    print(f"  ERROR: code={code}, body={str(body)[:200]}")

code, body = req(f"{BASE}:8105/api/paper-trading/orders", headers=auth)
if isinstance(body, dict):
    orders = body.get("orders", body.get("data", []))
    print(f"  orders: {len(orders)}")
else:
    print(f"  orders: code={code}")

print("\n=== DB HEALTH CHECKS ===")
for port, name in [(8104, "Portfolio"), (8102, "Watchlist"), (8105, "PaperTrading")]:
    code, body = req(f"{BASE}:{port}/health")
    db_status = body.get("database", body.get("db", "unknown")) if isinstance(body, dict) else "error"
    print(f"  {name}: health={code}, db={db_status}")

print("\nDone.")
