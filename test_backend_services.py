"""
Backend Services Automation Test Suite
Tests all FastAPI microservices
"""

import pytest
import requests
import time
from datetime import datetime

# Base URLs
BASE_URLS = {
    "user": "http://localhost:8001",
    "screener": "http://localhost:8002",
    "watchlist": "http://localhost:8003",
    "portfolio": "http://localhost:8004",
    "paper_trading": "http://localhost:8005"
}

# Test user credentials
TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPassword123!"
}

@pytest.fixture(scope="session")
def auth_token():
    """Register and login to get auth token"""
    # Register
    response = requests.post(
        f"{BASE_URLS['user']}/api/auth/signup",
        json=TEST_USER
    )
    assert response.status_code in [200, 201, 400], f"Registration failed: {response.text}"

    # Login
    response = requests.post(
        f"{BASE_URLS['user']}/api/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


class TestUserService:
    """Test User Service (Port 8001)"""
    
    def test_docs_accessible(self):
        """Test API documentation is accessible"""
        response = requests.get(f"{BASE_URLS['user']}/docs")
        assert response.status_code == 200
        assert "Swagger UI" in response.text
    
    def test_register_user(self):
        """Test user registration"""
        new_user = {
            "username": f"newuser_{int(time.time())}",
            "email": f"new_{int(time.time())}@example.com",
            "password": "NewPassword123!"
        }
        response = requests.post(
            f"{BASE_URLS['user']}/api/auth/signup",
            json=new_user
        )
        assert response.status_code in [200, 201]
    
    def test_login_user(self, auth_token):
        """Test user login"""
        assert auth_token is not None
        assert len(auth_token) > 0


class TestScreenerService:
    """Test Screener Service (Port 8002)"""
    
    def test_docs_accessible(self):
        """Test API documentation is accessible"""
        response = requests.get(f"{BASE_URLS['screener']}/docs")
        assert response.status_code == 200
    
    def test_get_sectors(self):
        """Test getting sectors list"""
        response = requests.get(f"{BASE_URLS['screener']}/api/screener/sectors")
        assert response.status_code == 200
        sectors = response.json()
        assert isinstance(sectors, list)
        assert len(sectors) > 5, "Should have at least 5 sectors"

    def test_search_stocks(self, auth_token):
        """Test stock search with filters"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        search_params = {
            "minPrice": 100,
            "maxPrice": 500
        }
        response = requests.post(
            f"{BASE_URLS['screener']}/api/screener/search",
            headers=headers,
            json=search_params
        )
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)


class TestWatchlistService:
    """Test Watchlist Service (Port 8003)"""
    
    def test_docs_accessible(self):
        """Test API documentation is accessible"""
        response = requests.get(f"{BASE_URLS['watchlist']}/docs")
        assert response.status_code == 200
    
    def test_get_watchlist(self, auth_token):
        """Test getting user watchlist"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URLS['watchlist']}/api/watchlist",
            headers=headers
        )
        assert response.status_code == 200
        watchlist = response.json()
        assert isinstance(watchlist, list)
    
    def test_add_to_watchlist(self, auth_token):
        """Test adding stock to watchlist"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URLS['watchlist']}/api/watchlist",
            headers=headers,
            json={"ticker": "AAPL"}
        )
        assert response.status_code in [200, 201]


class TestPortfolioService:
    """Test Portfolio Service (Port 8004)"""
    
    def test_docs_accessible(self):
        """Test API documentation is accessible"""
        response = requests.get(f"{BASE_URLS['portfolio']}/docs")
        assert response.status_code == 200
    
    def test_get_portfolio(self, auth_token):
        """Test getting user portfolio"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URLS['portfolio']}/api/portfolio",
            headers=headers
        )
        assert response.status_code == 200
        portfolio = response.json()
        assert "cash" in portfolio
        assert "positions" in portfolio
        assert "total_value" in portfolio
    
    def test_buy_stock(self, auth_token):
        """Test buying stock"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URLS['portfolio']}/api/portfolio/buy",
            headers=headers,
            json={"ticker": "AAPL", "quantity": 1}
        )
        assert response.status_code in [200, 201]


class TestPaperTradingService:
    """Test Paper Trading Service (Port 8005)"""
    
    def test_docs_accessible(self):
        """Test API documentation is accessible"""
        response = requests.get(f"{BASE_URLS['paper_trading']}/docs")
        assert response.status_code == 200
    
    def test_get_account(self, auth_token):
        """Test getting paper trading account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URLS['paper_trading']}/api/paper/account",
            headers=headers
        )
        assert response.status_code == 200
        account = response.json()
        assert "cash" in account
        assert "positions" in account
    
    def test_place_market_order(self, auth_token):
        """Test placing market order"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URLS['paper_trading']}/api/paper/order",
            headers=headers,
            json={
                "ticker": "TSLA",
                "side": "buy",
                "quantity": 1,
                "order_type": "market"
            }
        )
        assert response.status_code in [200, 201]

