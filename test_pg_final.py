#!/usr/bin/env python3
"""Final PG verification: all CRUD operations across 3 services."""
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1"
PASS = FAIL = 0

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

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  \033[32mPASS\033[0m {name}")
    else:
        FAIL += 1
        print(f"  \033[31mFAIL\033[0m {name} -- {detail}")

# Auth
code, body = req(f"{BASE}:8101/api/auth/login", method="POST",
                 data={"email": "kasireddymeruva@gmail.com", "password": "Kurichedu12345!"})
token = body.get("access_token", "") if isinstance(body, dict) else ""
auth = {"Authorization": f"Bearer {token}"}
test("AUTH: login", bool(token), f"code={code}")

# ============================================================
print("\n\033[1m=== PORTFOLIO (pg_only) ===\033[0m")

# Read portfolio
code, port = req(f"{BASE}:8104/api/portfolio", headers=auth)
test("PG-PORT-01: read portfolio", code == 200, f"code={code}")
if isinstance(port, dict):
    test("PG-PORT-02: has cash", "cash" in port, str(list(port.keys()))[:60])
    test("PG-PORT-03: has positions", "positions" in port, "")
    initial_cash = port.get("cash", 0)

# Buy stock
code, buy = req(f"{BASE}:8104/api/portfolio/buy", method="POST", headers=auth,
                data={"ticker": "GOOGL", "quantity": 2, "price": 0})
test("PG-PORT-04: buy GOOGL", code == 200, f"code={code}, body={str(buy)[:100]}")

# Verify position appears
code, port2 = req(f"{BASE}:8104/api/portfolio", headers=auth)
if isinstance(port2, dict):
    tickers = [p.get("ticker") for p in port2.get("positions", [])]
    test("PG-PORT-05: GOOGL in positions", "GOOGL" in tickers, str(tickers))
    test("PG-PORT-06: cash decreased", port2.get("cash", 0) < initial_cash, f"was {initial_cash}, now {port2.get('cash')}")

# Sell stock
code, sell = req(f"{BASE}:8104/api/portfolio/sell", method="POST", headers=auth,
                 data={"ticker": "GOOGL", "quantity": 2, "price": 0})
test("PG-PORT-07: sell GOOGL", code == 200, f"code={code}, body={str(sell)[:100]}")

# Transactions
code, txns = req(f"{BASE}:8104/api/portfolio/transactions", headers=auth)
test("PG-PORT-08: transactions", code == 200, f"code={code}")
if isinstance(txns, dict):
    tx_list = txns.get("transactions", txns.get("data", []))
    test("PG-PORT-09: has transactions", len(tx_list) > 0, f"count={len(tx_list)}")

# Performance
code, perf = req(f"{BASE}:8104/api/portfolio/performance", headers=auth)
test("PG-PORT-10: performance", code == 200, f"code={code}")

# ============================================================
print("\n\033[1m=== WATCHLIST (pg_only) ===\033[0m")

# Read watchlist
code, wl = req(f"{BASE}:8102/api/watchlist", headers=auth)
test("PG-WL-01: read watchlist", code == 200, f"code={code}")

# Add stock
code, add = req(f"{BASE}:8102/api/watchlist", method="POST", headers=auth,
                data={"ticker": "TSLA"})
test("PG-WL-02: add TSLA", code == 200, f"code={code}, body={str(add)[:100]}")

# Verify stock appears
code, wl2 = req(f"{BASE}:8102/api/watchlist", headers=auth)
if isinstance(wl2, list):
    tickers = [s.get("ticker") for s in wl2]
    test("PG-WL-03: TSLA in watchlist", "TSLA" in tickers, str(tickers))

# Delete stock
code, dl = req(f"{BASE}:8102/api/watchlist/TSLA", method="DELETE", headers=auth)
test("PG-WL-04: delete TSLA", code in (200, 204), f"code={code}")

# Verify removed
code, wl3 = req(f"{BASE}:8102/api/watchlist", headers=auth)
if isinstance(wl3, list):
    tickers = [s.get("ticker") for s in wl3]
    test("PG-WL-05: TSLA removed", "TSLA" not in tickers, str(tickers))

# All tickers endpoint
code, at = req(f"{BASE}:8102/api/watchlist/all-tickers")
test("PG-WL-06: all-tickers endpoint", code == 200, f"code={code}")

# Multi-watchlist: create a new list
code, new_list = req(f"{BASE}:8102/api/watchlists", method="POST", headers=auth,
                     data={"name": "Tech Stocks"})
test("PG-WL-07: create new watchlist", code in (200, 201), f"code={code}, body={str(new_list)[:100]}")

# List all watchlists
code, lists = req(f"{BASE}:8102/api/watchlists", headers=auth)
test("PG-WL-08: list watchlists", code == 200, f"code={code}")
if isinstance(lists, list):
    test("PG-WL-09: has multiple lists", len(lists) >= 2, f"count={len(lists)}")

# ============================================================
print("\n\033[1m=== PAPER TRADING (pg_only) ===\033[0m")

# Read account
code, acct = req(f"{BASE}:8105/api/paper/account", headers=auth)
test("PG-PT-01: read account", code == 200, f"code={code}")

# Place market buy
code, order = req(f"{BASE}:8105/api/paper/order", method="POST", headers=auth,
                  data={"ticker": "AAPL", "type": "market", "side": "buy", "quantity": 5})
test("PG-PT-02: place buy order", code in (200, 201), f"code={code}, body={str(order)[:200]}")

# Check account after buy
code, acct2 = req(f"{BASE}:8105/api/paper/account", headers=auth)
if isinstance(acct2, dict):
    test("PG-PT-03: has positions after buy", len(acct2.get("positions", [])) > 0,
         f"positions={len(acct2.get('positions', []))}")

# Place market sell
code, order2 = req(f"{BASE}:8105/api/paper/order", method="POST", headers=auth,
                   data={"ticker": "AAPL", "type": "market", "side": "sell", "quantity": 5})
test("PG-PT-04: place sell order", code in (200, 201), f"code={code}, body={str(order2)[:200]}")

# Order history
code, orders = req(f"{BASE}:8105/api/paper/orders", headers=auth)
test("PG-PT-05: order history", code == 200, f"code={code}")
if isinstance(orders, (dict, list)):
    order_list = orders if isinstance(orders, list) else orders.get("orders", [])
    test("PG-PT-06: has orders", len(order_list) > 0, f"count={len(order_list)}")

# Reset account
code, reset = req(f"{BASE}:8105/api/paper/reset", method="POST", headers=auth)
test("PG-PT-07: reset account", code == 200, f"code={code}, body={str(reset)[:100]}")

# Verify reset
code, acct3 = req(f"{BASE}:8105/api/paper/account", headers=auth)
if isinstance(acct3, dict):
    test("PG-PT-08: cash reset to 100k", abs(float(acct3.get("cash", 0)) - 100000) < 1,
         f"cash={acct3.get('cash')}")

# ============================================================
print(f"\n{'='*50}")
print(f"  PG WRITE VERIFICATION")
print(f"{'='*50}")
print(f"  \033[32mPASSED: {PASS}\033[0m")
print(f"  \033[31mFAILED: {FAIL}\033[0m")
print(f"  TOTAL:  {PASS + FAIL}")
print(f"{'='*50}")

import sys
sys.exit(1 if FAIL > 0 else 0)
