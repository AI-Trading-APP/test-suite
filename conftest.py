"""Root conftest — loads golden data and provides shared fixtures.

Supports two test environments controlled by the TEST_ENV environment variable:
  - TEST_ENV=local  (default) — runs against local Docker services on ports 8000-8009
  - TEST_ENV=test             — runs against test VPS at test.ktrading.tech, ports 8101-8110

Environment files:
  - local: ../.env.test.local  (auto-loaded if present)
  - test:  ../.env.test        (auto-loaded if present)
"""
import json
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Environment detection & env-file loading
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).parent
REPO_ROOT = TESTS_DIR.parent

# Determine active environment
TEST_ENV = os.getenv("TEST_ENV", "local").strip().lower()

# Load the matching env file (OS-level env vars always win — override=False)
_ENV_FILES = {
    "local": REPO_ROOT / ".env.test.local",
    "test": REPO_ROOT / ".env.test",
}
_env_file = _ENV_FILES.get(TEST_ENV, _ENV_FILES["local"])
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file, override=False)
    except ImportError:
        pass  # python-dotenv not installed; rely on OS-level env vars

# ---------------------------------------------------------------------------
# Service URL resolution
# ---------------------------------------------------------------------------
# Defaults per environment — can be overridden via env vars in the loaded file.
_DEFAULT_URLS: dict[str, dict[str, str]] = {
    "local": {
        "prediction_engine": "http://localhost:8000",
        "user":              "http://localhost:8001",
        "watchlist":         "http://localhost:8002",
        "screener":          "http://localhost:8003",
        "portfolio":         "http://localhost:8004",
        "paper_trading":     "http://localhost:8005",
        "analytics":         "http://localhost:8006",
        "subscription":      "http://localhost:8007",
        "referral":          "http://localhost:8008",
        "news":              "http://localhost:8009",
        "frontend":          "http://localhost:3000",
    },
    "test": {
        "prediction_engine": "http://127.0.0.1:8110",
        "user":              "http://127.0.0.1:8101",
        "watchlist":         "http://127.0.0.1:8102",
        "screener":          "http://127.0.0.1:8103",
        "portfolio":         "http://127.0.0.1:8104",
        "paper_trading":     "http://127.0.0.1:8105",
        "analytics":         "http://127.0.0.1:8106",
        "subscription":      "http://127.0.0.1:8107",
        "referral":          "http://127.0.0.1:8108",
        "news":              "http://127.0.0.1:8109",
        "frontend":          "http://127.0.0.1:3001",
    },
}

_defaults = _DEFAULT_URLS.get(TEST_ENV, _DEFAULT_URLS["local"])

# Allow individual URL overrides via env vars (e.g. USER_SERVICE_URL=http://...)
_SERVICE_URLS = {
    "prediction_engine": os.getenv("PREDICTION_ENGINE_URL",     _defaults["prediction_engine"]),
    "user":              os.getenv("USER_SERVICE_URL",           _defaults["user"]),
    "watchlist":         os.getenv("WATCHLIST_SERVICE_URL",      _defaults["watchlist"]),
    "screener":          os.getenv("SCREENER_SERVICE_URL",       _defaults["screener"]),
    "portfolio":         os.getenv("PORTFOLIO_SERVICE_URL",      _defaults["portfolio"]),
    "paper_trading":     os.getenv("PAPER_TRADING_SERVICE_URL",  _defaults["paper_trading"]),
    "analytics":         os.getenv("ANALYTICS_SERVICE_URL",      _defaults["analytics"]),
    "subscription":      os.getenv("SUBSCRIPTION_SERVICE_URL",   _defaults["subscription"]),
    "referral":          os.getenv("REFERRAL_SERVICE_URL",       _defaults["referral"]),
    "news":              os.getenv("NEWS_SERVICE_URL",            _defaults["news"]),
    "frontend":          os.getenv("FRONTEND_URL",               _defaults["frontend"]),
}

# Make tests/mocks and tests/factories importable
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(TESTS_DIR))

GOLDEN_DIR = TESTS_DIR / "golden"


# ---------------------------------------------------------------------------
# Environment fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_env():
    """Returns the active test environment: 'local' or 'test'."""
    return TEST_ENV


@pytest.fixture(scope="session")
def service_urls():
    """Returns a dict of service base URLs resolved for the active TEST_ENV.

    Override any URL by setting the corresponding environment variable before
    running pytest (e.g. USER_SERVICE_URL=http://...).
    """
    return _SERVICE_URLS


# ---------------------------------------------------------------------------
# Golden data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def golden_users():
    with open(GOLDEN_DIR / "users.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_stocks():
    with open(GOLDEN_DIR / "stocks.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_portfolios():
    with open(GOLDEN_DIR / "portfolios.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_paper_accounts():
    with open(GOLDEN_DIR / "paper_accounts.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_watchlists():
    with open(GOLDEN_DIR / "watchlists.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_predictions():
    with open(GOLDEN_DIR / "predictions.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_news():
    with open(GOLDEN_DIR / "news_articles.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_referrals():
    with open(GOLDEN_DIR / "referrals.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_subscriptions():
    with open(GOLDEN_DIR / "subscriptions.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_transactions():
    with open(GOLDEN_DIR / "transactions.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def golden_backtests():
    with open(GOLDEN_DIR / "backtest_results.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Common test helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def test_ticker():
    return "AAPL"


@pytest.fixture
def test_tickers():
    return ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]

