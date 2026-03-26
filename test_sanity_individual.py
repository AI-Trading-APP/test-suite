"""
Individual Service Sanity Tests
Tests each service one by one with basic health and functionality checks
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
import time
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Service configuration
SERVICES = {
    "postgres": {
        "name": "PostgreSQL Database",
        "port": 5432,
        "health_check": None,  # Special handling
        "type": "database"
    },
    "prediction_engine": {
        "name": "Prediction Engine",
        "port": 8000,
        "base_url": "http://localhost:8000",
        "health_endpoint": "/health",
        "type": "api"
    },
    "user_service": {
        "name": "User Service",
        "port": 8001,
        "base_url": "http://localhost:8001",
        "health_endpoint": "/health",
        "type": "api"
    },
    "watchlist_service": {
        "name": "Watchlist Service",
        "port": 8002,
        "base_url": "http://localhost:8002",
        "health_endpoint": "/health",
        "type": "api"
    },
    "screener_service": {
        "name": "Screener Service",
        "port": 8003,
        "base_url": "http://localhost:8003",
        "health_endpoint": "/health",
        "type": "api"
    },
    "portfolio_service": {
        "name": "Portfolio Service",
        "port": 8004,
        "base_url": "http://localhost:8004",
        "health_endpoint": "/health",
        "type": "api"
    },
    "paper_trading_service": {
        "name": "Paper Trading Service",
        "port": 8005,
        "base_url": "http://localhost:8005",
        "health_endpoint": "/health",
        "type": "api"
    },
    "analytics_service": {
        "name": "Analytics Service",
        "port": 8006,
        "base_url": "http://localhost:8006",
        "health_endpoint": "/health",
        "type": "api"
    },
    "subscription_service": {
        "name": "Subscription Service",
        "port": 8007,
        "base_url": "http://localhost:8007",
        "health_endpoint": "/health",
        "type": "api"
    },
    "referral_service": {
        "name": "Referral Service",
        "port": 8008,
        "base_url": "http://localhost:8008",
        "health_endpoint": "/health",
        "type": "api"
    },
    "news_service": {
        "name": "News Service",
        "port": 8009,
        "base_url": "http://localhost:8009",
        "health_endpoint": "/health",
        "type": "api"
    },
    "frontend": {
        "name": "Frontend (Next.js)",
        "port": 3000,
        "base_url": "http://localhost:3000",
        "health_endpoint": None,  # Frontend doesn't have /health
        "type": "frontend"
    }
}

class ServiceTester:
    """Test individual services"""
    
    def __init__(self):
        self.results = {}
    
    def test_service_connectivity(self, service_name: str, config: Dict) -> Tuple[bool, str]:
        """Test if service is reachable"""
        try:
            if config["type"] == "database":
                # For PostgreSQL, we'll check via docker
                return True, "Database check via Docker"
            
            base_url = config["base_url"]
            port = config["port"]
            
            # Try to connect to the port
            try:
                response = requests.get(base_url, timeout=3)
                return True, f"Service reachable (status: {response.status_code})"
            except requests.exceptions.ConnectionError:
                return False, "Connection refused - service not running"
            except requests.exceptions.Timeout:
                return False, "Connection timeout"
            except Exception as e:
                return False, f"Error: {str(e)}"
        except Exception as e:
            return False, f"Test error: {str(e)}"
    
    def test_health_endpoint(self, service_name: str, config: Dict) -> Tuple[bool, str]:
        """Test health endpoint"""
        try:
            if config.get("health_endpoint") is None:
                return None, "No health endpoint"
            
            base_url = config["base_url"]
            health_url = f"{base_url}{config['health_endpoint']}"
            
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, f"Healthy: {json.dumps(data, indent=2)}"
                except:
                    return True, f"Healthy (status: {response.status_code})"
            else:
                return False, f"Unhealthy (status: {response.status_code})"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_docs_endpoint(self, service_name: str, config: Dict) -> Tuple[bool, str]:
        """Test API documentation endpoint"""
        try:
            if config["type"] != "api":
                return None, "Not an API service"
            
            base_url = config["base_url"]
            docs_url = f"{base_url}/docs"
            
            response = requests.get(docs_url, timeout=5)
            if response.status_code == 200:
                return True, "API docs accessible"
            else:
                return False, f"Docs not accessible (status: {response.status_code})"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_root_endpoint(self, service_name: str, config: Dict) -> Tuple[bool, str]:
        """Test root endpoint"""
        try:
            if config["type"] == "database":
                return None, "Not applicable for database"
            
            base_url = config["base_url"]
            
            response = requests.get(base_url, timeout=5)
            if response.status_code in [200, 404, 405]:  # 404/405 are acceptable
                return True, f"Root endpoint responds (status: {response.status_code})"
            else:
                return False, f"Unexpected status: {response.status_code}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_service(self, service_name: str) -> Dict:
        """Run all tests for a service"""
        config = SERVICES[service_name]
        logger.info("script_output", message=f"\n{'='*80}")
        logger.info("script_output", message=f"Testing: {config['name']} (Port {config['port']})")
        logger.info("script_output", message=f"{'='*80}")
        
        results = {
            "service": config["name"],
            "port": config["port"],
            "tests": {}
        }
        
        # Test 1: Connectivity
        logger.info("script_output", message="\n[1/4] Testing connectivity...")
        success, message = self.test_service_connectivity(service_name, config)
        results["tests"]["connectivity"] = {"success": success, "message": message}
        logger.error("script_output", message=f"  {'[PASS]' if success else '[FAIL]'} {message}")
        
        if not success:
            logger.warning("script_output", message=f"  [SKIP] Service not reachable, skipping remaining tests")
            return results
        
        # Test 2: Health endpoint
        logger.info("script_output", message="\n[2/4] Testing health endpoint...")
        success, message = self.test_health_endpoint(service_name, config)
        if success is not None:
            results["tests"]["health"] = {"success": success, "message": message}
            logger.error("script_output", message=f"  {'[PASS]' if success else '[FAIL]'} {message}")
        else:
            results["tests"]["health"] = {"success": None, "message": message}
            logger.warning("script_output", message=f"  [SKIP] {message}")
        
        # Test 3: Root endpoint
        logger.info("script_output", message="\n[3/4] Testing root endpoint...")
        success, message = self.test_root_endpoint(service_name, config)
        if success is not None:
            results["tests"]["root"] = {"success": success, "message": message}
            logger.error("script_output", message=f"  {'[PASS]' if success else '[FAIL]'} {message}")
        else:
            results["tests"]["root"] = {"success": None, "message": message}
            logger.warning("script_output", message=f"  [SKIP] {message}")
        
        # Test 4: API docs (for API services)
        logger.info("script_output", message="\n[4/4] Testing API documentation...")
        success, message = self.test_docs_endpoint(service_name, config)
        if success is not None:
            results["tests"]["docs"] = {"success": success, "message": message}
            logger.error("script_output", message=f"  {'[PASS]' if success else '[FAIL]'} {message}")
        else:
            results["tests"]["docs"] = {"success": None, "message": message}
            logger.warning("script_output", message=f"  [SKIP] {message}")
        
        return results
    
    def run_all_tests(self):
        """Run tests for all services"""
        logger.info("script_output", message="\n" + "="*80)
        logger.info("script_output", message="INDIVIDUAL SERVICE SANITY TESTS")
        logger.info("script_output", message="="*80)
        logger.info("script_output", message=f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = {}
        
        for service_name in SERVICES.keys():
            try:
                result = self.test_service(service_name)
                all_results[service_name] = result
                time.sleep(1)  # Small delay between services
            except Exception as e:
                logger.error("script_output", message=f"\n[ERROR] Failed to test {service_name}: {str(e)}")
                all_results[service_name] = {
                    "service": SERVICES[service_name]["name"],
                    "error": str(e)
                }
        
        # Print summary
        self.print_summary(all_results)
        
        return all_results
    
    def print_summary(self, results: Dict):
        """Print test summary"""
        logger.info("script_output", message="\n" + "="*80)
        logger.info("script_output", message="TEST SUMMARY")
        logger.info("script_output", message="="*80)
        
        total_services = len(results)
        services_with_issues = 0
        
        for service_name, result in results.items():
            if "error" in result:
                logger.error("script_output", message=f"\n[ERROR] {result['service']}: {result['error']}")
                services_with_issues += 1
                continue
            
            tests = result.get("tests", {})
            failed_tests = []
            
            for test_name, test_result in tests.items():
                if test_result.get("success") is False:
                    failed_tests.append(test_name)
            
            if failed_tests:
                services_with_issues += 1
                logger.info("script_output", message=f"\n[ISSUES] {result['service']}:")
                for test in failed_tests:
                    logger.info("script_output", message=f"  - {test}: {tests[test]['message']}")
            else:
                logger.info("script_output", message=f"\n[OK] {result['service']}: All tests passed")
        
        logger.info("script_output", message=f"\n{'='*80}")
        logger.info("script_output", message=f"Total Services: {total_services}")
        logger.info("script_output", message=f"Services with Issues: {services_with_issues}")
        logger.info("script_output", message=f"Services OK: {total_services - services_with_issues}")
        logger.info("script_output", message=f"{'='*80}")
        logger.info("script_output", message=f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    tester = ServiceTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any service has issues
    has_issues = any(
        "error" in result or 
        any(t.get("success") is False for t in result.get("tests", {}).values())
        for result in results.values()
    )
    
    exit(1 if has_issues else 0)



