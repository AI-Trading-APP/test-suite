"""
Pytest configuration and shared fixtures
"""

import pytest
import requests
import time

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


@pytest.fixture(scope="session", autouse=True)
def check_services_running():
    """Check that all required services are running before tests"""
    services = {
        "User Service": "http://localhost:8001/docs",
        "Screener Service": "http://localhost:8002/docs",
        "Watchlist Service": "http://localhost:8003/docs",
        "Portfolio Service": "http://localhost:8004/docs",
        "Paper Trading Service": "http://localhost:8005/docs",
        "Frontend": "http://localhost:3000"
    }
    
    failed_services = []
    
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=3)
            if response.status_code != 200:
                failed_services.append(name)
        except requests.exceptions.RequestException:
            failed_services.append(name)
    
    if failed_services:
        pytest.exit(
            f"The following services are not running: {', '.join(failed_services)}\n"
            f"Please start all services before running tests."
        )


@pytest.fixture(scope="session")
def base_urls():
    """Base URLs for all services"""
    return {
        "user": "http://localhost:8001",
        "screener": "http://localhost:8002",
        "watchlist": "http://localhost:8003",
        "portfolio": "http://localhost:8004",
        "paper_trading": "http://localhost:8005",
        "frontend": "http://localhost:3000"
    }


@pytest.fixture
def test_ticker():
    """A reliable test ticker"""
    return "AAPL"


@pytest.fixture
def test_tickers():
    """Multiple test tickers"""
    return ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]

