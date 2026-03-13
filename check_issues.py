#!/usr/bin/env python3
"""Quick check for the 6 failing test issues."""
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

# 1. PE invalid key - what code do we get?
code, body = req(f"{BASE}:8110/v1/auth/token", method="POST", data={"api_key": "bad-key"})
print(f"PE invalid key: code={code}, body={str(body)[:200]}")

# 2. PE predictions/all - check total field
code, tok = req(f"{BASE}:8110/v1/auth/token", method="POST", data={"api_key": "predict-dev-key"})
token = tok.get("access_token", "") if isinstance(tok, dict) else ""
auth = {"Authorization": f"Bearer {token}"}

code, body = req(f"{BASE}:8110/v1/predictions/all?page=1&page_size=3", headers=auth)
if isinstance(body, dict):
    meta = {k: v for k, v in body.items() if k != "predictions"}
    print(f"PE predictions/all meta: {json.dumps(meta)}")
    print(f"PE predictions/all num_preds: {len(body.get('predictions', {}))}")

# 3. PE backtests/all with predictor token vs admin token
code, body = req(f"{BASE}:8110/v1/backtests/all?page=1&page_size=2", headers=auth)
print(f"PE backtests/all (predictor): code={code}")

code2, tok2 = req(f"{BASE}:8110/v1/auth/token", method="POST", data={"api_key": "admin-dev-key"})
admin_token = tok2.get("access_token", "") if isinstance(tok2, dict) else ""
admin_auth = {"Authorization": f"Bearer {admin_token}"}
code, body = req(f"{BASE}:8110/v1/backtests/all?page=1&page_size=2", headers=admin_auth)
print(f"PE backtests/all (admin): code={code}, body={str(body)[:200]}")

# 4. Screener - what endpoints exist for sp500?
for path in ["/api/screener/sp500", "/api/screener/search", "/api/screener/ai-screener", "/api/screener/sectors"]:
    code, body = req(f"{BASE}:8103{path}")
    print(f"Screener {path}: code={code}, body={str(body)[:100]}")

# 5. Frontend routes
for path in ["/auth/login", "/auth/signup", "/auth/register", "/login", "/register", "/signin", "/signup"]:
    code, _ = req(f"{BASE}:3001{path}")
    print(f"FE {path}: code={code}")

# 6. User service login with real creds
code, body = req(f"{BASE}:8101/api/auth/login", method="POST", data={"email": "kasireddymeruva@gmail.com", "password": "Kurichedu12345!"})
print(f"US login real creds: code={code}, body={str(body)[:200]}")
