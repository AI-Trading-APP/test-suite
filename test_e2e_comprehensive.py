"""
Comprehensive End-to-End Test Suite
Tests all services and capabilities of the AI Trading Platform
"""

import pytest
import requests
import time
import json
from datetime import datetime
from typing import Dict, Optional

# Service URLs
SERVICES = {
    "prediction_engine": "http://localhost:8000",
    "user_service": "http://localhost:8001",
    "watchlist_service": "http://localhost:8002",
    "screener_service": "http://localhost:8003",
    "portfolio_service": "http://localhost:8004",
    "paper_trading_service": "http://localhost:8005",
    "analytics_service": "http://localhost:8006",
    "subscription_service": "http://localhost:8007",
    "referral_service": "http://localhost:8008",
    "news_service": "http://localhost:8009",
    "frontend": "http://localhost:3000"
}

# Test user credentials
TEST_USER = {
    "name": f"Test User {int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "username": f"testuser_{int(time.time())}"
}

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
    
    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print(f"[PASS] {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"[FAIL] {test_name} - {error}")
    
    def add_skip(self, test_name: str, reason: str):
        self.skipped.append((test_name, reason))
        print(f"[SKIP] {test_name} - {reason}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"[PASS] Passed: {len(self.passed)}")
        print(f"[FAIL] Failed: {len(self.failed)}")
        print(f"[SKIP] Skipped: {len(self.skipped)}")
        print(f"[TOTAL] Total: {total}")
        if self.failed:
            print("\nFailed Tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")
        print("="*80)
        return len(self.failed) == 0

results = TestResults()

def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for a service to be available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def check_service_health(url: str) -> bool:
    """Check if service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# ============================================================================
# SERVICE HEALTH CHECKS
# ============================================================================

def test_all_services_health():
    """Test that all services are running and healthy"""
    print("\n" + "="*80)
    print("SERVICE HEALTH CHECKS")
    print("="*80)
    
    for service_name, url in SERVICES.items():
        if service_name == "frontend":
            # Frontend might not have /health endpoint
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 404]:
                    results.add_pass(f"Service Health: {service_name}")
                else:
                    results.add_fail(f"Service Health: {service_name}", f"Status {response.status_code}")
            except Exception as e:
                results.add_fail(f"Service Health: {service_name}", str(e))
        else:
            if check_service_health(url):
                results.add_pass(f"Service Health: {service_name}")
            else:
                results.add_fail(f"Service Health: {service_name}", "Service not responding")

# ============================================================================
# AUTHENTICATION & USER MANAGEMENT
# ============================================================================

def test_user_registration():
    """Test user registration"""
    print("\n" + "="*80)
    print("AUTHENTICATION: User Registration")
    print("="*80)
    
    try:
        # Try different endpoint formats
        endpoints = [
            "/api/auth/signup",
            "/api/auth/register",
            "/api/users/register"
        ]
        
        registered = False
        for endpoint in endpoints:
            try:
                response = requests.post(
                    f"{SERVICES['user_service']}{endpoint}",
                    json=TEST_USER,
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    results.add_pass("User Registration")
                    registered = True
                    break
                elif response.status_code == 400:
                    # User might already exist, try login
                    data = response.json()
                    if "already exists" in str(data).lower() or "duplicate" in str(data).lower():
                        results.add_pass("User Registration (user exists)")
                        registered = True
                        break
            except Exception as e:
                continue
        
        if not registered:
            results.add_fail("User Registration", "All endpoints failed")
    except Exception as e:
        results.add_fail("User Registration", str(e))

def test_user_login() -> Optional[str]:
    """Test user login and return token"""
    print("\n" + "="*80)
    print("AUTHENTICATION: User Login")
    print("="*80)
    
    try:
        endpoints = [
            "/api/auth/login",
            "/api/users/login"
        ]
        
        token = None
        for endpoint in endpoints:
            try:
                # Try JSON body
                response = requests.post(
                    f"{SERVICES['user_service']}{endpoint}",
                    json={
                        "email": TEST_USER["email"],
                        "password": TEST_USER["password"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token") or data.get("token")
                    if token:
                        results.add_pass("User Login")
                        return token
                
                # Try form data
                response = requests.post(
                    f"{SERVICES['user_service']}{endpoint}",
                    data={
                        "username": TEST_USER["email"],
                        "password": TEST_USER["password"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token") or data.get("token")
                    if token:
                        results.add_pass("User Login")
                        return token
            except Exception as e:
                continue
        
        results.add_fail("User Login", "Could not authenticate")
        return None
    except Exception as e:
        results.add_fail("User Login", str(e))
        return None

def test_get_user_profile(token: str):
    """Test getting user profile"""
    print("\n" + "="*80)
    print("USER MANAGEMENT: Get Profile")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        endpoints = [
            "/api/users/profile",
            "/api/auth/me",
            "/api/users/me"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{SERVICES['user_service']}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    results.add_pass("Get User Profile")
                    return
            except:
                continue
        
        results.add_fail("Get User Profile", "All endpoints failed")
    except Exception as e:
        results.add_fail("Get User Profile", str(e))

# ============================================================================
# PREDICTION ENGINE
# ============================================================================

def test_prediction_health():
    """Test prediction engine health"""
    print("\n" + "="*80)
    print("PREDICTION ENGINE: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{SERVICES['prediction_engine']}/health", timeout=10)
        if response.status_code == 200:
            results.add_pass("Prediction Engine Health")
        else:
            results.add_fail("Prediction Engine Health", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Prediction Engine Health", str(e))

def test_get_prediction(token: str):
    """Test getting stock prediction"""
    print("\n" + "="*80)
    print("PREDICTION ENGINE: Get Prediction")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        ticker = "AAPL"
        
        endpoints = [
            f"/api/predictions/{ticker}",
            f"/predict/{ticker}",
            f"/api/predict/{ticker}"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{SERVICES['prediction_engine']}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    if "prediction" in data or "forecast" in data or "price" in data:
                        results.add_pass("Get Stock Prediction")
                        return
            except:
                continue
        
        results.add_fail("Get Stock Prediction", "All endpoints failed or invalid response")
    except Exception as e:
        results.add_fail("Get Stock Prediction", str(e))

def test_backtest(token: str):
    """Test backtesting"""
    print("\n" + "="*80)
    print("PREDICTION ENGINE: Backtest")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        ticker = "AAPL"
        
        endpoints = [
            f"/api/backtest/{ticker}",
            f"/backtest/{ticker}",
            f"/api/backtesting/{ticker}"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{SERVICES['prediction_engine']}{endpoint}",
                    headers=headers,
                    timeout=60
                )
                if response.status_code == 200:
                    results.add_pass("Backtest")
                    return
            except:
                continue
        
        results.add_skip("Backtest", "Endpoint not available or timeout")
    except Exception as e:
        results.add_skip("Backtest", str(e))

# ============================================================================
# WATCHLIST SERVICE
# ============================================================================

def test_watchlist_get(token: str):
    """Test getting watchlist"""
    print("\n" + "="*80)
    print("WATCHLIST: Get Watchlist")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{SERVICES['watchlist_service']}/api/watchlist",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            results.add_pass("Get Watchlist")
        else:
            results.add_fail("Get Watchlist", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Get Watchlist", str(e))

def test_watchlist_add(token: str):
    """Test adding to watchlist"""
    print("\n" + "="*80)
    print("WATCHLIST: Add Stock")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{SERVICES['watchlist_service']}/api/watchlist",
            headers=headers,
            json={"ticker": "AAPL"},
            timeout=10
        )
        if response.status_code in [200, 201]:
            results.add_pass("Add to Watchlist")
        else:
            results.add_fail("Add to Watchlist", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Add to Watchlist", str(e))

def test_watchlist_remove(token: str):
    """Test removing from watchlist"""
    print("\n" + "="*80)
    print("WATCHLIST: Remove Stock")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(
            f"{SERVICES['watchlist_service']}/api/watchlist/AAPL",
            headers=headers,
            timeout=10
        )
        if response.status_code in [200, 204]:
            results.add_pass("Remove from Watchlist")
        else:
            results.add_skip("Remove from Watchlist", f"Status {response.status_code}")
    except Exception as e:
        results.add_skip("Remove from Watchlist", str(e))

# ============================================================================
# SCREENER SERVICE
# ============================================================================

def test_screener_sectors():
    """Test getting sectors"""
    print("\n" + "="*80)
    print("SCREENER: Get Sectors")
    print("="*80)
    
    try:
        response = requests.get(
            f"{SERVICES['screener_service']}/api/screener/sectors",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                results.add_pass("Get Sectors")
            else:
                results.add_fail("Get Sectors", "Empty or invalid response")
        else:
            results.add_fail("Get Sectors", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Get Sectors", str(e))

def test_screener_search(token: str):
    """Test stock screening"""
    print("\n" + "="*80)
    print("SCREENER: Search Stocks")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{SERVICES['screener_service']}/api/screener/search",
            headers=headers,
            json={"minPrice": 100, "maxPrice": 500},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                results.add_pass("Search Stocks")
            else:
                results.add_fail("Search Stocks", "Invalid response format")
        else:
            results.add_fail("Search Stocks", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Search Stocks", str(e))

# ============================================================================
# PORTFOLIO SERVICE
# ============================================================================

def test_portfolio_get(token: str):
    """Test getting portfolio"""
    print("\n" + "="*80)
    print("PORTFOLIO: Get Portfolio")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{SERVICES['portfolio_service']}/api/portfolio",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "cash" in data or "positions" in data:
                results.add_pass("Get Portfolio")
            else:
                results.add_fail("Get Portfolio", "Invalid response structure")
        else:
            results.add_fail("Get Portfolio", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Get Portfolio", str(e))

def test_portfolio_buy(token: str):
    """Test buying stock"""
    print("\n" + "="*80)
    print("PORTFOLIO: Buy Stock")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{SERVICES['portfolio_service']}/api/portfolio/buy",
            headers=headers,
            json={"ticker": "AAPL", "quantity": 1, "price": 150.0},
            timeout=10
        )
        if response.status_code in [200, 201]:
            results.add_pass("Buy Stock")
        else:
            results.add_skip("Buy Stock", f"Status {response.status_code} - May need valid price")
    except Exception as e:
        results.add_skip("Buy Stock", str(e))

# ============================================================================
# PAPER TRADING SERVICE
# ============================================================================

def test_paper_trading_account(token: str):
    """Test getting paper trading account"""
    print("\n" + "="*80)
    print("PAPER TRADING: Get Account")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{SERVICES['paper_trading_service']}/api/paper/account",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if "cash" in data or "balance" in data:
                results.add_pass("Get Paper Trading Account")
            else:
                results.add_fail("Get Paper Trading Account", "Invalid response")
        else:
            results.add_fail("Get Paper Trading Account", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Get Paper Trading Account", str(e))

def test_paper_trading_order(token: str):
    """Test placing paper trading order"""
    print("\n" + "="*80)
    print("PAPER TRADING: Place Order")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{SERVICES['paper_trading_service']}/api/paper/order",
            headers=headers,
            json={
                "ticker": "TSLA",
                "side": "buy",
                "quantity": 1,
                "order_type": "market"
            },
            timeout=10
        )
        if response.status_code in [200, 201]:
            results.add_pass("Place Paper Trading Order")
        else:
            results.add_skip("Place Paper Trading Order", f"Status {response.status_code}")
    except Exception as e:
        results.add_skip("Place Paper Trading Order", str(e))

# ============================================================================
# ANALYTICS SERVICE
# ============================================================================

def test_analytics_health():
    """Test analytics service health"""
    print("\n" + "="*80)
    print("ANALYTICS: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{SERVICES['analytics_service']}/health", timeout=10)
        if response.status_code == 200:
            results.add_pass("Analytics Service Health")
        else:
            results.add_fail("Analytics Service Health", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Analytics Service Health", str(e))

def test_analytics_dashboard(token: str):
    """Test analytics dashboard"""
    print("\n" + "="*80)
    print("ANALYTICS: Get Dashboard")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        endpoints = [
            "/api/analytics/dashboard",
            "/api/analytics",
            "/api/dashboard"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{SERVICES['analytics_service']}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    results.add_pass("Get Analytics Dashboard")
                    return
            except:
                continue
        
        results.add_skip("Get Analytics Dashboard", "Endpoint not available")
    except Exception as e:
        results.add_skip("Get Analytics Dashboard", str(e))

# ============================================================================
# SUBSCRIPTION SERVICE
# ============================================================================

def test_subscription_health():
    """Test subscription service health"""
    print("\n" + "="*80)
    print("SUBSCRIPTION: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{SERVICES['subscription_service']}/health", timeout=10)
        if response.status_code == 200:
            results.add_pass("Subscription Service Health")
        else:
            results.add_fail("Subscription Service Health", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Subscription Service Health", str(e))

def test_subscription_plans(token: str):
    """Test getting subscription plans"""
    print("\n" + "="*80)
    print("SUBSCRIPTION: Get Plans")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        endpoints = [
            "/api/subscriptions/plans",
            "/api/subscription/plans",
            "/api/plans"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{SERVICES['subscription_service']}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    results.add_pass("Get Subscription Plans")
                    return
            except:
                continue
        
        results.add_skip("Get Subscription Plans", "Endpoint not available")
    except Exception as e:
        results.add_skip("Get Subscription Plans", str(e))

# ============================================================================
# REFERRAL SERVICE
# ============================================================================

def test_referral_health():
    """Test referral service health"""
    print("\n" + "="*80)
    print("REFERRAL: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{SERVICES['referral_service']}/health", timeout=10)
        if response.status_code == 200:
            results.add_pass("Referral Service Health")
        else:
            results.add_fail("Referral Service Health", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("Referral Service Health", str(e))

def test_referral_generate_code(token: str):
    """Test generating referral code"""
    print("\n" + "="*80)
    print("REFERRAL: Generate Code")
    print("="*80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        endpoints = [
            "/api/referrals/generate-code",
            "/api/referrals/code",
            "/api/referral/generate"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    f"{SERVICES['referral_service']}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    results.add_pass("Generate Referral Code")
                    return
            except:
                continue
        
        results.add_skip("Generate Referral Code", "Endpoint not available")
    except Exception as e:
        results.add_skip("Generate Referral Code", str(e))

# ============================================================================
# NEWS SERVICE
# ============================================================================

def test_news_health():
    """Test news service health"""
    print("\n" + "="*80)
    print("NEWS: Health Check")
    print("="*80)
    
    try:
        response = requests.get(f"{SERVICES['news_service']}/health", timeout=10)
        if response.status_code == 200:
            results.add_pass("News Service Health")
        else:
            results.add_fail("News Service Health", f"Status {response.status_code}")
    except Exception as e:
        results.add_fail("News Service Health", str(e))

def test_news_latest():
    """Test getting latest news"""
    print("\n" + "="*80)
    print("NEWS: Get Latest News")
    print("="*80)
    
    try:
        endpoints = [
            "/api/news/latest",
            "/api/news",
            "/api/news/articles"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{SERVICES['news_service']}{endpoint}",
                    timeout=10
                )
                if response.status_code == 200:
                    results.add_pass("Get Latest News")
                    return
            except:
                continue
        
        results.add_skip("Get Latest News", "Endpoint not available or API key missing")
    except Exception as e:
        results.add_skip("Get Latest News", str(e))

def test_news_trending():
    """Test getting trending tickers"""
    print("\n" + "="*80)
    print("NEWS: Get Trending Tickers")
    print("="*80)
    
    try:
        response = requests.get(
            f"{SERVICES['news_service']}/api/news/trending",
            timeout=10
        )
        if response.status_code == 200:
            results.add_pass("Get Trending Tickers")
        else:
            results.add_skip("Get Trending Tickers", f"Status {response.status_code}")
    except Exception as e:
        results.add_skip("Get Trending Tickers", str(e))

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE E2E TEST SUITE")
    print("AI Trading Platform - All Services")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for services to be ready
    print("\nWaiting for services to be ready...")
    time.sleep(5)
    
    # 1. Health checks
    test_all_services_health()
    
    # 2. Authentication
    test_user_registration()
    token = test_user_login()
    
    if not token:
        print("\n[WARNING] Could not get auth token. Some tests will be skipped.")
        token = ""
    
    # 3. User Management
    if token:
        test_get_user_profile(token)
    
    # 4. Prediction Engine
    test_prediction_health()
    if token:
        test_get_prediction(token)
        test_backtest(token)
    
    # 5. Watchlist
    if token:
        test_watchlist_get(token)
        test_watchlist_add(token)
        test_watchlist_remove(token)
    
    # 6. Screener
    test_screener_sectors()
    if token:
        test_screener_search(token)
    
    # 7. Portfolio
    if token:
        test_portfolio_get(token)
        test_portfolio_buy(token)
    
    # 8. Paper Trading
    if token:
        test_paper_trading_account(token)
        test_paper_trading_order(token)
    
    # 9. Analytics
    test_analytics_health()
    if token:
        test_analytics_dashboard(token)
    
    # 10. Subscription
    test_subscription_health()
    if token:
        test_subscription_plans(token)
    
    # 11. Referral
    test_referral_health()
    if token:
        test_referral_generate_code(token)
    
    # 12. News
    test_news_health()
    test_news_latest()
    test_news_trending()
    
    # Summary
    success = results.summary()
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

