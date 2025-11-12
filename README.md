# AI Trading Platform - Automated Test Suite

Comprehensive automated testing suite for the AI Trading Platform microservices.

## 📋 Test Coverage

### Backend Tests (`test_backend_services.py`)
- **User Service (Port 8001)**
  - API documentation accessibility
  - User registration
  - User login
  - JWT token generation

- **Screener Service (Port 8002)**
  - API documentation accessibility
  - Stock list retrieval (100+ stocks)
  - Stock search with filters
  - Real-time price data

- **Watchlist Service (Port 8003)**
  - API documentation accessibility
  - Get user watchlist
  - Add stocks to watchlist
  - Remove stocks from watchlist

- **Portfolio Service (Port 8004)**
  - API documentation accessibility
  - Get portfolio
  - Buy stocks
  - Sell stocks
  - Transaction history
  - P&L calculations

- **Paper Trading Service (Port 8005)**
  - API documentation accessibility
  - Get account
  - Place market orders
  - Place limit orders
  - Order history
  - Account reset

### Frontend E2E Tests (`test_frontend_e2e.py`)
- **Dashboard Page**
  - Page loads successfully
  - Navigation links work
  - Service cards displayed

- **Portfolio Page**
  - Page loads successfully
  - Summary cards visible
  - Buy stock form
  - Sell stock form
  - Positions table
  - Transaction history

- **Paper Trading Page**
  - Page loads successfully
  - Account summary visible
  - Market order form
  - Limit order form
  - Positions table
  - Order history
  - Reset account button

- **Responsive Design**
  - Mobile viewport (375x667)
  - Tablet viewport (768x1024)
  - Desktop viewport (1920x1080)

### Integration Tests (`test_integration.py`)
- **Portfolio Workflow**
  - Complete buy/sell workflow
  - Portfolio updates correctly
  - Transaction history tracking
  - P&L calculations

- **Paper Trading Workflow**
  - Place market orders
  - Place limit orders
  - Account updates correctly
  - Order history tracking

- **Watchlist Integration**
  - Add stocks from screener to watchlist
  - Cross-service data flow

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- All services running (ports 8001-8005, 3000)

### Installation

```powershell
# Navigate to tests directory
cd tests

# Run the automated test script
.\run_tests.ps1
```

The script will:
1. Create a virtual environment
2. Install dependencies
3. Install Playwright browsers
4. Check service status
5. Run selected tests
6. Generate HTML report

### Manual Setup

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## 🧪 Running Tests

### Run All Tests
```powershell
pytest -v
```

### Run Specific Test Suite
```powershell
# Backend tests only
pytest test_backend_services.py -v

# Frontend E2E tests only
pytest test_frontend_e2e.py -v

# Integration tests only
pytest test_integration.py -v
```

### Run Specific Test Class
```powershell
pytest test_backend_services.py::TestUserService -v
pytest test_frontend_e2e.py::TestPortfolioPage -v
```

### Run Specific Test
```powershell
pytest test_backend_services.py::TestUserService::test_register_user -v
```

### Run with HTML Report
```powershell
pytest -v --html=test_report.html --self-contained-html
```

### Run Tests in Parallel
```powershell
pytest -v -n auto
```

### Run Quick Smoke Tests
```powershell
pytest -v -k "test_docs_accessible or test_page_loads"
```

## 📊 Test Reports

After running tests, an HTML report is generated:
- **test_report.html** - Comprehensive test results
- Includes pass/fail status
- Detailed error messages
- Execution time
- Screenshots (for E2E tests)

Open the report in your browser:
```powershell
Start-Process test_report.html
```

## 🔧 Configuration

### pytest.ini
Configure pytest behavior:
- Test discovery patterns
- Output verbosity
- HTML report settings
- Custom markers

### conftest.py
Shared fixtures and configuration:
- Service availability check
- Base URLs
- Test data
- Authentication tokens

## 📝 Writing New Tests

### Backend Test Example
```python
class TestNewService:
    def test_endpoint(self, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            "http://localhost:8006/api/endpoint",
            headers=headers
        )
        assert response.status_code == 200
```

### Frontend E2E Test Example
```python
class TestNewPage:
    def test_page_loads(self, page: Page):
        page.goto("http://localhost:3000/new-page")
        expect(page.locator("text=New Page")).to_be_visible()
```

## 🐛 Troubleshooting

### Services Not Running
```
Error: The following services are not running...
```
**Solution:** Start all services before running tests

### Playwright Browser Not Installed
```
Error: Executable doesn't exist at ...
```
**Solution:** Run `playwright install chromium`

### Authentication Failures
```
Error: 401 Unauthorized
```
**Solution:** Check that User Service is running and registration/login works

### Timeout Errors
```
Error: Timeout 30000ms exceeded
```
**Solution:** Increase timeout or check if service is slow to respond

## 📈 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    cd tests
    pip install -r requirements.txt
    playwright install chromium
    pytest -v --html=test_report.html
```

## 🎯 Test Markers

Use markers to categorize tests:
```powershell
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run only E2E tests
pytest -m e2e
```

## 📚 Dependencies

- **pytest** - Testing framework
- **pytest-playwright** - Browser automation
- **playwright** - E2E testing
- **requests** - HTTP client
- **pytest-html** - HTML reports
- **pytest-xdist** - Parallel execution

## 🔒 Security Notes

- Test users are created with unique timestamps
- Test data is isolated per test run
- No production data is used
- Authentication tokens are session-scoped

## 📞 Support

For issues or questions:
1. Check service logs
2. Verify all services are running
3. Check test report for detailed errors
4. Review service API documentation

---

**Last Updated:** 2025-11-13  
**Version:** 1.0.0  
**Workspace:** c:\Users\Tejana\Personal_Projects\AI-Trading-APP

