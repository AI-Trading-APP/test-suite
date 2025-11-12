#!/bin/bash
# AI Trading Platform - Automated Test Runner (Linux/Mac)

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   AI Trading Platform - Automated Test Suite            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing test dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
playwright install chromium

# Check if services are running
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Checking Service Status                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

services=(
    "User Service:8001"
    "Screener Service:8002"
    "Watchlist Service:8003"
    "Portfolio Service:8004"
    "Paper Trading:8005"
    "Frontend:3000"
)

all_running=true
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port" | grep -q "200\|404"; then
        echo "  ✓ $name (Port $port): RUNNING"
    else
        echo "  ✗ $name (Port $port): NOT RUNNING"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    echo ""
    echo "⚠ WARNING: Not all services are running!"
    echo "Please start all services before running tests."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Running Test Suite                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test selection menu
echo "Select test suite to run:"
echo "  1. All tests (Backend + Frontend + Integration)"
echo "  2. Backend tests only"
echo "  3. Frontend E2E tests only"
echo "  4. Integration tests only"
echo "  5. Quick smoke tests"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Running all tests..."
        pytest -v --html=test_report.html --self-contained-html
        ;;
    2)
        echo ""
        echo "Running backend tests..."
        pytest test_backend_services.py -v --html=backend_test_report.html --self-contained-html
        ;;
    3)
        echo ""
        echo "Running frontend E2E tests..."
        pytest test_frontend_e2e.py -v --html=frontend_test_report.html --self-contained-html
        ;;
    4)
        echo ""
        echo "Running integration tests..."
        pytest test_integration.py -v --html=integration_test_report.html --self-contained-html
        ;;
    5)
        echo ""
        echo "Running quick smoke tests..."
        pytest -v -k "test_docs_accessible or test_page_loads" --html=smoke_test_report.html --self-contained-html
        ;;
    *)
        echo ""
        echo "Invalid choice. Running all tests..."
        pytest -v --html=test_report.html --self-contained-html
        ;;
esac

# Display results
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Test Complete                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "Test report generated: test_report.html"
echo "Open the report in your browser to view detailed results."
echo ""

# Ask to open report
read -p "Open test report in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open > /dev/null; then
        xdg-open test_report.html
    elif command -v open > /dev/null; then
        open test_report.html
    else
        echo "Please open test_report.html manually"
    fi
fi

