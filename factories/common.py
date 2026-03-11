"""Common test utilities."""
import random
import string
import uuid


def random_string(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@test.ktrading.tech"


def random_ticker() -> str:
    """Generate a random 3-4 letter ticker symbol."""
    length = random.choice([3, 4])
    return ''.join(random.choices(string.ascii_uppercase, k=length))


GOLDEN_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "UNH", "XOM", "WMT", "SPY"]
