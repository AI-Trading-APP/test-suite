# AI Trading Platform - Automated Test Runner
# This script runs all automated tests

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   AI Trading Platform - Automated Test Suite            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`nInstalling test dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install Playwright browsers
Write-Host "`nInstalling Playwright browsers..." -ForegroundColor Yellow
playwright install chromium

# Check if services are running
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              Checking Service Status                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$services = @(
    @{Name="User Service"; Port=8001},
    @{Name="Screener Service"; Port=8002},
    @{Name="Watchlist Service"; Port=8003},
    @{Name="Portfolio Service"; Port=8004},
    @{Name="Paper Trading"; Port=8005},
    @{Name="Frontend"; Port=3000}
)

$allRunning = $true
foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        Write-Host "  ✓ $($service.Name) (Port $($service.Port)): RUNNING" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $($service.Name) (Port $($service.Port)): NOT RUNNING" -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host "`n⚠ WARNING: Not all services are running!" -ForegroundColor Yellow
    Write-Host "Please start all services before running tests.`n" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Run tests
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                  Running Test Suite                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Test selection menu
Write-Host "Select test suite to run:" -ForegroundColor Yellow
Write-Host "  1. All tests (Backend + Frontend + Integration)" -ForegroundColor White
Write-Host "  2. Backend tests only" -ForegroundColor White
Write-Host "  3. Frontend E2E tests only" -ForegroundColor White
Write-Host "  4. Integration tests only" -ForegroundColor White
Write-Host "  5. Quick smoke tests" -ForegroundColor White

$choice = Read-Host "`nEnter choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`nRunning all tests..." -ForegroundColor Cyan
        pytest -v --html=test_report.html --self-contained-html
    }
    "2" {
        Write-Host "`nRunning backend tests..." -ForegroundColor Cyan
        pytest test_backend_services.py -v --html=backend_test_report.html --self-contained-html
    }
    "3" {
        Write-Host "`nRunning frontend E2E tests..." -ForegroundColor Cyan
        pytest test_frontend_e2e.py -v --html=frontend_test_report.html --self-contained-html
    }
    "4" {
        Write-Host "`nRunning integration tests..." -ForegroundColor Cyan
        pytest test_integration.py -v --html=integration_test_report.html --self-contained-html
    }
    "5" {
        Write-Host "`nRunning quick smoke tests..." -ForegroundColor Cyan
        pytest -v -k "test_docs_accessible or test_page_loads" --html=smoke_test_report.html --self-contained-html
    }
    default {
        Write-Host "`nInvalid choice. Running all tests..." -ForegroundColor Yellow
        pytest -v --html=test_report.html --self-contained-html
    }
}

# Display results
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    Test Complete                         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "Test report generated: test_report.html" -ForegroundColor Green
Write-Host "Open the report in your browser to view detailed results.`n" -ForegroundColor White

# Ask to open report
$openReport = Read-Host "Open test report in browser? (y/n)"
if ($openReport -eq "y") {
    Start-Process "test_report.html"
}

