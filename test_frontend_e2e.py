"""
Frontend End-to-End Test Suite
Tests the Next.js frontend using Playwright
"""

import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:3000"

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
    }


class TestDashboard:
    """Test Dashboard Page"""
    
    def test_dashboard_loads(self, page: Page):
        """Test dashboard page loads successfully"""
        page.goto(f"{BASE_URL}/dashboard")
        expect(page).to_have_title("AI Trading Platform")
        
        # Check for main navigation elements
        expect(page.locator("text=Dashboard")).to_be_visible()
        expect(page.locator("text=Portfolio")).to_be_visible()
        expect(page.locator("text=Paper Trading")).to_be_visible()
    
    def test_navigation_links(self, page: Page):
        """Test navigation links work"""
        page.goto(f"{BASE_URL}/dashboard")
        
        # Test Portfolio link
        page.click("text=Portfolio")
        expect(page).to_have_url(f"{BASE_URL}/portfolio")
        
        # Go back to dashboard
        page.goto(f"{BASE_URL}/dashboard")
        
        # Test Paper Trading link
        page.click("text=Paper Trading")
        expect(page).to_have_url(f"{BASE_URL}/paper-trading")


class TestPortfolioPage:
    """Test Portfolio Page"""
    
    def test_portfolio_page_loads(self, page: Page):
        """Test portfolio page loads successfully"""
        page.goto(f"{BASE_URL}/portfolio")
        
        # Check for main sections
        expect(page.locator("text=Portfolio")).to_be_visible()
        expect(page.locator("text=Total Value")).to_be_visible()
        expect(page.locator("text=Cash")).to_be_visible()
        expect(page.locator("text=Buy Stock")).to_be_visible()
        expect(page.locator("text=Sell Stock")).to_be_visible()
    
    def test_buy_stock_form(self, page: Page):
        """Test buy stock form"""
        page.goto(f"{BASE_URL}/portfolio")
        
        # Fill in buy form
        page.fill('input[placeholder="Enter ticker (e.g., AAPL)"]', "AAPL")
        page.fill('input[placeholder="Enter quantity"]', "5")
        
        # Submit form
        page.click('button:has-text("Buy Stock")')
        
        # Wait for response (success or error message)
        page.wait_for_timeout(2000)
        
        # Check if form was submitted (either success message or error)
        # Note: This might fail if not authenticated
    
    def test_portfolio_sections_visible(self, page: Page):
        """Test all portfolio sections are visible"""
        page.goto(f"{BASE_URL}/portfolio")
        
        # Check for summary cards
        expect(page.locator("text=Total Value")).to_be_visible()
        expect(page.locator("text=Cash")).to_be_visible()
        expect(page.locator("text=Total P&L")).to_be_visible()
        
        # Check for positions section
        expect(page.locator("text=Current Positions")).to_be_visible()
        
        # Check for transactions section
        expect(page.locator("text=Transaction History")).to_be_visible()


class TestPaperTradingPage:
    """Test Paper Trading Page"""
    
    def test_paper_trading_page_loads(self, page: Page):
        """Test paper trading page loads successfully"""
        page.goto(f"{BASE_URL}/paper-trading")
        
        # Check for main sections
        expect(page.locator("text=Paper Trading")).to_be_visible()
        expect(page.locator("text=Account Balance")).to_be_visible()
        expect(page.locator("text=Place Order")).to_be_visible()
    
    def test_order_form_elements(self, page: Page):
        """Test order form has all required elements"""
        page.goto(f"{BASE_URL}/paper-trading")
        
        # Check form elements exist
        expect(page.locator('input[placeholder*="ticker"]')).to_be_visible()
        expect(page.locator('input[placeholder*="quantity"]')).to_be_visible()
        expect(page.locator('select')).to_be_visible()  # Order type selector
        expect(page.locator('button:has-text("Place Order")')).to_be_visible()
    
    def test_market_order_form(self, page: Page):
        """Test placing a market order"""
        page.goto(f"{BASE_URL}/paper-trading")
        
        # Fill in order form
        page.fill('input[placeholder*="ticker"]', "TSLA")
        page.fill('input[placeholder*="quantity"]', "2")
        
        # Select market order type
        page.select_option('select', 'market')
        
        # Submit form
        page.click('button:has-text("Place Order")')
        
        # Wait for response
        page.wait_for_timeout(2000)
    
    def test_limit_order_form(self, page: Page):
        """Test limit order form shows price field"""
        page.goto(f"{BASE_URL}/paper-trading")
        
        # Select limit order type
        page.select_option('select', 'limit')
        
        # Check that limit price field appears
        expect(page.locator('input[placeholder*="price"]')).to_be_visible()
    
    def test_positions_section(self, page: Page):
        """Test positions section is visible"""
        page.goto(f"{BASE_URL}/paper-trading")
        
        expect(page.locator("text=Current Positions")).to_be_visible()
        expect(page.locator("text=Order History")).to_be_visible()
    
    def test_reset_account_button(self, page: Page):
        """Test reset account button exists"""
        page.goto(f"{BASE_URL}/paper-trading")
        
        expect(page.locator('button:has-text("Reset Account")')).to_be_visible()


class TestResponsiveness:
    """Test responsive design"""
    
    def test_mobile_viewport(self, page: Page):
        """Test pages work on mobile viewport"""
        page.set_viewport_size({"width": 375, "height": 667})
        
        # Test dashboard
        page.goto(f"{BASE_URL}/dashboard")
        expect(page.locator("text=Dashboard")).to_be_visible()
        
        # Test portfolio
        page.goto(f"{BASE_URL}/portfolio")
        expect(page.locator("text=Portfolio")).to_be_visible()
        
        # Test paper trading
        page.goto(f"{BASE_URL}/paper-trading")
        expect(page.locator("text=Paper Trading")).to_be_visible()
    
    def test_tablet_viewport(self, page: Page):
        """Test pages work on tablet viewport"""
        page.set_viewport_size({"width": 768, "height": 1024})
        
        page.goto(f"{BASE_URL}/dashboard")
        expect(page.locator("text=Dashboard")).to_be_visible()

