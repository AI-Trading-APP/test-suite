"""Root conftest — loads golden data and provides shared fixtures."""
import json
import sys
from pathlib import Path

import pytest

# Make tests/mocks and tests/factories importable
TESTS_DIR = Path(__file__).parent
sys.path.insert(0, str(TESTS_DIR.parent))
sys.path.insert(0, str(TESTS_DIR))

GOLDEN_DIR = TESTS_DIR / "golden"


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


@pytest.fixture
def test_ticker():
    return "AAPL"


@pytest.fixture
def test_tickers():
    return ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]


@pytest.fixture(scope="session")
def service_urls():
    """Test service URLs for integration tests."""
    return {
        "user": "http://127.0.0.1:8101",
        "watchlist": "http://127.0.0.1:8102",
        "screener": "http://127.0.0.1:8103",
        "portfolio": "http://127.0.0.1:8104",
        "paper_trading": "http://127.0.0.1:8105",
        "analytics": "http://127.0.0.1:8106",
        "subscription": "http://127.0.0.1:8107",
        "referral": "http://127.0.0.1:8108",
        "news": "http://127.0.0.1:8109",
        "prediction_engine": "http://127.0.0.1:8110",
    }
