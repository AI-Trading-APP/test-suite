"""
Integration Test Conftest
- Provides in-process FastAPI TestClients for each service
- Patches external deps (yfinance, etc.)
- JWT auth helpers for cross-service token validation

NOTE: portfolio and paper-trading services use mock verify_token that
always returns {"user_id": "user_1"}, so auth_headers are not verified
by those services but we pass them for consistency.
Watchlist service uses real JWT verification.
"""

import os
import sys
import json
import jwt as pyjwt
import pytest
import types
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent.parent

for service_dir in [
    "watchlistservice", "portfolioservice", "papertradingservice",
    "analyticsservice",
]:
    svc_path = str(ROOT / service_dir)
    if svc_path not in sys.path:
        sys.path.insert(0, svc_path)

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
JWT_SECRET = "test-jwt-secret-for-integration-tests-1234"


def make_jwt(user_id=1, email="integration@test.ktrading.tech"):
    payload = {
        "user_id": user_id,
        "email": email,
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=2),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture()
def auth_headers():
    return {"Authorization": f"Bearer {make_jwt()}"}


@pytest.fixture()
def second_user_headers():
    return {"Authorization": f"Bearer {make_jwt(user_id=2, email='user2@test.ktrading.tech')}"}


# ---------------------------------------------------------------------------
# Mock yfinance
# ---------------------------------------------------------------------------
MOCK_PRICES = {
    "AAPL": 230.0, "MSFT": 415.0, "GOOGL": 175.0, "AMZN": 185.0,
    "NVDA": 880.0, "META": 500.0, "TSLA": 250.0, "JPM": 195.0,
    "UNH": 520.0, "XOM": 110.0, "WMT": 170.0, "SPY": 510.0,
}


def _make_mock_ticker(symbol):
    price = MOCK_PRICES.get(symbol.upper(), 100.0)
    mock = MagicMock()
    # Return DataFrame with all standard columns so history endpoints work
    hist_df = pd.DataFrame({
        "Open": [price * 0.99],
        "High": [price * 1.01],
        "Low": [price * 0.98],
        "Close": [price],
        "Volume": [1_000_000],
    }, index=pd.DatetimeIndex([datetime.utcnow()]))
    mock.history.return_value = hist_df
    mock.info = {
        "shortName": f"{symbol} Inc.",
        "sector": "Technology",
        "marketCap": 2_000_000_000_000,
        "trailingPE": 30.0,
        "currentPrice": price,
        "regularMarketPrice": price,
    }
    return mock


@pytest.fixture(autouse=True)
def _patch_yfinance():
    with patch("yfinance.Ticker", side_effect=_make_mock_ticker), \
         patch("yfinance.download", return_value=pd.DataFrame()):
        yield


# ---------------------------------------------------------------------------
# Fake price_cache module (shared by portfolio and paper trading)
# ---------------------------------------------------------------------------
def _ensure_fake_price_cache():
    if "price_cache" not in sys.modules or not hasattr(sys.modules["price_cache"], "price_cache"):
        mock_pc = types.ModuleType("price_cache")

        class _FakePC:
            def get(self, k): return None, False
            def get_stale(self, k): return None
            def set(self, k, v, t): pass
            def stats(self): return {"hits": 0, "misses": 0, "size": 0}

        mock_pc.price_cache = _FakePC()
        mock_pc.company_cache = _FakePC()
        mock_pc.PRICE_TTL = 30
        mock_pc.COMPANY_NAME_TTL = 86400
        sys.modules["price_cache"] = mock_pc
    else:
        # Ensure company_cache exists even if module was previously created
        mod = sys.modules["price_cache"]
        if not hasattr(mod, "company_cache"):
            class _FakePC:
                def get(self, k): return None, False
                def get_stale(self, k): return None
                def set(self, k, v, t): pass
                def stats(self): return {"hits": 0, "misses": 0, "size": 0}
            mod.company_cache = _FakePC()
            mod.COMPANY_NAME_TTL = 86400


# ---------------------------------------------------------------------------
# Portfolio Service TestClient
# ---------------------------------------------------------------------------
@pytest.fixture()
def portfolio_client(tmp_path):
    _ensure_fake_price_cache()
    import importlib
    import portfolioservice.main as pmod
    importlib.reload(pmod)
    pmod.PORTFOLIOS_FILE = str(tmp_path / "portfolios.json")

    from fastapi.testclient import TestClient
    yield TestClient(pmod.app)


# ---------------------------------------------------------------------------
# Paper Trading Service TestClient
# ---------------------------------------------------------------------------
@pytest.fixture()
def paper_client(tmp_path):
    _ensure_fake_price_cache()
    import importlib
    import papertradingservice.main as ptmod
    importlib.reload(ptmod)
    ptmod.PAPER_ACCOUNTS_FILE = str(tmp_path / "paper_accounts.json")

    from fastapi.testclient import TestClient
    yield TestClient(ptmod.app)


# ---------------------------------------------------------------------------
# Watchlist Service TestClient (uses real JWT verification)
# ---------------------------------------------------------------------------
@pytest.fixture()
def watchlist_client(tmp_path):
    import importlib
    import watchlistservice.main as wmod
    importlib.reload(wmod)
    wmod.WATCHLISTS_FILE = str(tmp_path / "watchlists.json")
    # Patch JWT secret so our test tokens are accepted
    # watchlist main.py uses SECRET_KEY (from JWT_SECRET_KEY env var)
    wmod.SECRET_KEY = JWT_SECRET
    if hasattr(wmod, "JWT_SECRET"):
        wmod.JWT_SECRET = JWT_SECRET
    if hasattr(wmod, "JWT_SECRET_KEY"):
        wmod.JWT_SECRET_KEY = JWT_SECRET

    from fastapi.testclient import TestClient
    yield TestClient(wmod.app)


# ---------------------------------------------------------------------------
# Analytics Service TestClient (no auth required)
# ---------------------------------------------------------------------------
@pytest.fixture()
def analytics_client():
    import importlib
    import analyticsservice.main as amod
    importlib.reload(amod)

    # Mock the portfolio service HTTP calls that analytics makes
    mock_portfolio_resp = MagicMock()
    mock_portfolio_resp.status_code = 200
    mock_portfolio_resp.json.return_value = {
        "cash": 95000.0,
        "positions": [
            {"ticker": "AAPL", "quantity": 10, "avgCostBasis": 220.0}
        ],
        "totalValue": 97300.0,
    }
    mock_portfolio_resp.raise_for_status = MagicMock()

    mock_txn_resp = MagicMock()
    mock_txn_resp.status_code = 200
    mock_txn_resp.json.return_value = {
        "transactions": [
            {"type": "buy", "ticker": "AAPL", "quantity": 10, "price": 220.0,
             "timestamp": "2026-02-01T10:00:00Z"},
        ]
    }
    mock_txn_resp.raise_for_status = MagicMock()

    def _requests_get_side_effect(url, **kwargs):
        if "transactions" in url:
            return mock_txn_resp
        return mock_portfolio_resp

    # Patch requests.get in the analytics module namespace
    with patch("analyticsservice.main.requests.get", side_effect=_requests_get_side_effect):
        from fastapi.testclient import TestClient
        yield TestClient(amod.app)
