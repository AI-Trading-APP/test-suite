"""
Quick Sanity Test - Run without pytest
Tests all services are responding correctly
"""

from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).resolve().parent
for import_path in (CURRENT_DIR, CURRENT_DIR.parent, CURRENT_DIR.parent.parent):
    import_path_str = str(import_path)
    if import_path_str not in sys.path:
        sys.path.insert(0, import_path_str)

from ai_trading_common.logging_config import setup_logging, get_logger

setup_logging("test-suite")
logger = get_logger()


import requests
import sys
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    logger.info("script_output", message=f"\n{CYAN}{BOLD}{'='*60}{RESET}")
    logger.info("script_output", message=f"{CYAN}{BOLD}{text.center(60)}{RESET}")
    logger.info("script_output", message=f"{CYAN}{BOLD}{'='*60}{RESET}\n")

def print_success(text):
    logger.info("script_output", message=f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    logger.info("script_output", message=f"{RED}✗ {text}{RESET}")

def print_info(text):
    logger.info("script_output", message=f"{YELLOW}ℹ {text}{RESET}")

def test_service(name, url, expected_status=200):
    """Test if a service endpoint is responding"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print_success(f"{name}: RUNNING (Status {response.status_code})")
            return True
        else:
            print_error(f"{name}: Unexpected status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"{name}: NOT RESPONDING (Connection refused)")
        return False
    except requests.exceptions.Timeout:
        print_error(f"{name}: TIMEOUT (Service too slow)")
        return False
    except Exception as e:
        print_error(f"{name}: ERROR ({str(e)})")
        return False

def test_api_endpoint(name, url, expected_key=None):
    """Test API endpoint and check response"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if expected_key and expected_key in data:
                print_success(f"{name}: WORKING (Found '{expected_key}')")
                return True
            elif isinstance(data, list):
                print_success(f"{name}: WORKING ({len(data)} items)")
                return True
            else:
                print_success(f"{name}: WORKING")
                return True
        else:
            print_error(f"{name}: Status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{name}: ERROR ({str(e)})")
        return False

def main():
    print_header("AI Trading Platform - Quick Sanity Test")
    logger.info("script_output", message=f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Test 1: User Service
    logger.info("script_output", message=f"{BOLD}[1/6] Testing User Service (Port 8001){RESET}")
    result = test_service("User Service API Docs", "http://localhost:8001/docs")
    results.append(("User Service", result))
    
    # Test 2: Screener Service
    logger.info("script_output", message=f"\n{BOLD}[2/6] Testing Screener Service (Port 8002){RESET}")
    result1 = test_service("Screener API Docs", "http://localhost:8002/docs")
    result2 = test_api_endpoint("Screener Sectors API", "http://localhost:8002/api/screener/sectors")
    results.append(("Screener Service", result1 and result2))
    
    # Test 3: Watchlist Service
    logger.info("script_output", message=f"\n{BOLD}[3/6] Testing Watchlist Service (Port 8003){RESET}")
    result = test_service("Watchlist API Docs", "http://localhost:8003/docs")
    results.append(("Watchlist Service", result))
    
    # Test 4: Portfolio Service
    logger.info("script_output", message=f"\n{BOLD}[4/6] Testing Portfolio Service (Port 8004){RESET}")
    result = test_service("Portfolio API Docs", "http://localhost:8004/docs")
    results.append(("Portfolio Service", result))
    
    # Test 5: Paper Trading Service
    logger.info("script_output", message=f"\n{BOLD}[5/6] Testing Paper Trading Service (Port 8005){RESET}")
    result = test_service("Paper Trading API Docs", "http://localhost:8005/docs")
    results.append(("Paper Trading Service", result))
    
    # Test 6: Frontend
    logger.info("script_output", message=f"\n{BOLD}[6/6] Testing Frontend (Port 3000){RESET}")
    result = test_service("Frontend", "http://localhost:3000")
    results.append(("Frontend", result))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for service, result in results:
        if result:
            print_success(f"{service}: PASSED")
        else:
            print_error(f"{service}: FAILED")
    
    logger.info("script_output", message=f"\n{CYAN}{BOLD}{'='*60}{RESET}")
    if passed == total:
        logger.info("script_output", message=f"{GREEN}{BOLD}✓ ALL {total} SERVICES PASSED - SYSTEM READY!{RESET}")
    else:
        logger.info("script_output", message=f"{YELLOW}{BOLD}⚠ {passed}/{total} SERVICES PASSED{RESET}")
    logger.info("script_output", message=f"{CYAN}{BOLD}{'='*60}{RESET}\n")
    
    # Service URLs
    logger.info("script_output", message=f"{BOLD}Service URLs:{RESET}")
    logger.info("script_output", message=f"  • Frontend:        http://localhost:3000")
    logger.info("script_output", message=f"  • User Service:    http://localhost:8001/docs")
    logger.info("script_output", message=f"  • Screener:        http://localhost:8002/docs")
    logger.info("script_output", message=f"  • Watchlist:       http://localhost:8003/docs")
    logger.info("script_output", message=f"  • Portfolio:       http://localhost:8004/docs")
    logger.info("script_output", message=f"  • Paper Trading:   http://localhost:8005/docs\n")
    
    # Exit code
    if passed == total:
        print_info("Run full test suite with: pytest -v")
        sys.exit(0)
    else:
        print_error("Some services failed. Please check and restart them.")
        sys.exit(1)

if __name__ == "__main__":
    main()

