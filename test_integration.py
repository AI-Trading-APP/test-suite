"""
Integration Test Suite
Tests end-to-end workflows across multiple services
"""

import pytest
import requests
import time

BASE_URLS = {
    "user": "http://localhost:8001",
    "screener": "http://localhost:8002",
    "watchlist": "http://localhost:8003",
    "portfolio": "http://localhost:8004",
    "paper_trading": "http://localhost:8005"
}

@pytest.fixture(scope="module")
def test_user():
    """Create a test user for integration tests"""
    user = {
        "username": f"integration_test_{int(time.time())}",
        "email": f"integration_{int(time.time())}@example.com",
        "password": "IntegrationTest123!"
    }
    
    # Register
    response = requests.post(
        f"{BASE_URLS['user']}/api/auth/register",
        json=user
    )
    assert response.status_code in [200, 201, 400]
    
    # Login
    response = requests.post(
        f"{BASE_URLS['user']}/api/auth/login",
        data={
            "username": user["username"],
            "password": user["password"]
        }
    )
    assert response.status_code == 200
    token = response.json().get("access_token")
    
    return {"user": user, "token": token}


class TestPortfolioWorkflow:
    """Test complete portfolio workflow"""
    
    def test_complete_buy_sell_workflow(self, test_user):
        """Test buying and selling stocks"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # 1. Get initial portfolio
        response = requests.get(
            f"{BASE_URLS['portfolio']}/api/portfolio",
            headers=headers
        )
        assert response.status_code == 200
        initial_portfolio = response.json()
        initial_cash = initial_portfolio.get("cash", 10000)
        
        # 2. Buy stock
        buy_response = requests.post(
            f"{BASE_URLS['portfolio']}/api/portfolio/buy",
            headers=headers,
            json={"ticker": "AAPL", "quantity": 5}
        )
        assert buy_response.status_code in [200, 201]
        
        # 3. Verify portfolio updated
        time.sleep(1)  # Wait for update
        response = requests.get(
            f"{BASE_URLS['portfolio']}/api/portfolio",
            headers=headers
        )
        assert response.status_code == 200
        updated_portfolio = response.json()
        
        # Check that cash decreased
        assert updated_portfolio["cash"] < initial_cash
        
        # Check that position exists
        positions = updated_portfolio.get("positions", [])
        aapl_position = next((p for p in positions if p["ticker"] == "AAPL"), None)
        assert aapl_position is not None
        assert aapl_position["quantity"] >= 5
        
        # 4. Get transactions
        response = requests.get(
            f"{BASE_URLS['portfolio']}/api/portfolio/transactions",
            headers=headers
        )
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) > 0
        
        # 5. Sell some stock
        sell_response = requests.post(
            f"{BASE_URLS['portfolio']}/api/portfolio/sell",
            headers=headers,
            json={"ticker": "AAPL", "quantity": 2}
        )
        assert sell_response.status_code in [200, 201]
        
        # 6. Verify position updated
        time.sleep(1)
        response = requests.get(
            f"{BASE_URLS['portfolio']}/api/portfolio",
            headers=headers
        )
        assert response.status_code == 200
        final_portfolio = response.json()
        
        positions = final_portfolio.get("positions", [])
        aapl_position = next((p for p in positions if p["ticker"] == "AAPL"), None)
        if aapl_position:
            assert aapl_position["quantity"] == 3  # 5 bought - 2 sold


class TestPaperTradingWorkflow:
    """Test complete paper trading workflow"""
    
    def test_complete_trading_workflow(self, test_user):
        """Test placing orders and managing positions"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # 1. Get initial account
        response = requests.get(
            f"{BASE_URLS['paper_trading']}/api/paper/account",
            headers=headers
        )
        assert response.status_code == 200
        initial_account = response.json()
        initial_cash = initial_account.get("cash", 100000)
        
        # 2. Place market buy order
        order_response = requests.post(
            f"{BASE_URLS['paper_trading']}/api/paper/order",
            headers=headers,
            json={
                "ticker": "TSLA",
                "side": "buy",
                "quantity": 3,
                "order_type": "market"
            }
        )
        assert order_response.status_code in [200, 201]
        
        # 3. Verify account updated
        time.sleep(1)
        response = requests.get(
            f"{BASE_URLS['paper_trading']}/api/paper/account",
            headers=headers
        )
        assert response.status_code == 200
        updated_account = response.json()
        
        # Check cash decreased
        assert updated_account["cash"] < initial_cash
        
        # Check position exists
        positions = updated_account.get("positions", [])
        tsla_position = next((p for p in positions if p["ticker"] == "TSLA"), None)
        assert tsla_position is not None
        assert tsla_position["quantity"] == 3
        
        # 4. Get order history
        response = requests.get(
            f"{BASE_URLS['paper_trading']}/api/paper/orders",
            headers=headers
        )
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) > 0
        
        # 5. Place limit order
        limit_order = requests.post(
            f"{BASE_URLS['paper_trading']}/api/paper/order",
            headers=headers,
            json={
                "ticker": "AAPL",
                "side": "buy",
                "quantity": 5,
                "order_type": "limit",
                "limit_price": 150.00
            }
        )
        assert limit_order.status_code in [200, 201]


class TestWatchlistIntegration:
    """Test watchlist integration with screener"""
    
    def test_add_screened_stock_to_watchlist(self, test_user):
        """Test adding a stock from screener to watchlist"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # 1. Get stocks from screener
        response = requests.get(f"{BASE_URLS['screener']}/api/screener/stocks")
        assert response.status_code == 200
        stocks = response.json()
        assert len(stocks) > 0
        
        # 2. Pick a stock
        test_ticker = stocks[0]["ticker"]
        
        # 3. Add to watchlist
        response = requests.post(
            f"{BASE_URLS['watchlist']}/api/watchlist",
            headers=headers,
            json={"ticker": test_ticker}
        )
        assert response.status_code in [200, 201]
        
        # 4. Verify it's in watchlist
        response = requests.get(
            f"{BASE_URLS['watchlist']}/api/watchlist",
            headers=headers
        )
        assert response.status_code == 200
        watchlist = response.json()
        
        tickers = [item["ticker"] for item in watchlist]
        assert test_ticker in tickers

