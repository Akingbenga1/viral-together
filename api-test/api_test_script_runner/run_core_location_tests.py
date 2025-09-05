#!/usr/bin/env python3
"""
Core Location Operations Test Runner
Tests the basic location functionality including geocoding and search endpoints
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoreLocationTestRunner:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        })
        
    def test_geocode_address(self, address: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        """Test geocoding an address to coordinates"""
        url = f"{self.base_url}/api/v1/geocode"
        payload = {"address": address}
        if country_code:
            payload["country_code"] = country_code
            
        logger.info(f"Testing geocoding: {address}")
        response = self.session.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Geocoding successful: {result}")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Geocoding failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Test reverse geocoding coordinates to address"""
        url = f"{self.base_url}/api/v1/reverse-geocode"
        payload = {"latitude": latitude, "longitude": longitude}
        
        logger.info(f"Testing reverse geocoding: {latitude}, {longitude}")
        response = self.session.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Reverse geocoding successful: {result}")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Reverse geocoding failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_search_locations(self, query: str, country_code: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Test location search functionality"""
        url = f"{self.base_url}/api/v1/search"
        params = {"query": query, "limit": limit}
        if country_code:
            params["country_code"] = country_code
            
        logger.info(f"Testing location search: {query} (limit: {limit})")
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Location search successful: {len(result)} results")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Location search failed: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all core location operation tests"""
        logger.info("🚀 Starting Core Location Operations Tests")
        
        test_results = {
            "geocoding_tests": [],
            "reverse_geocoding_tests": [],
            "search_tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
        
        # Test geocoding
        result = self.test_geocode_address("123 Main Street, New York, NY", "US")
        test_results["geocoding_tests"].append(result)
        
        result = self.test_geocode_address("10 Downing Street, London", "GB")
        test_results["geocoding_tests"].append(result)
        
        # Test reverse geocoding
        result = self.test_reverse_geocode(40.7128, -74.0060)
        test_results["reverse_geocoding_tests"].append(result)
        
        result = self.test_reverse_geocode(51.5074, -0.1278)
        test_results["reverse_geocoding_tests"].append(result)
        
        # Test location search
        result = self.test_search_locations("New York", limit=10)
        test_results["search_tests"].append(result)
        
        result = self.test_search_locations("London", "GB", 5)
        test_results["search_tests"].append(result)
        
        # Calculate summary
        all_tests = (test_results["geocoding_tests"] + 
                    test_results["reverse_geocoding_tests"] + 
                    test_results["search_tests"])
        
        test_results["summary"]["total"] = len(all_tests)
        test_results["summary"]["passed"] = sum(1 for test in all_tests if test.get("success", False))
        test_results["summary"]["failed"] = test_results["summary"]["total"] - test_results["summary"]["passed"]
        
        logger.info(f"📊 Test Summary: {test_results['summary']['passed']}/{test_results['summary']['total']} tests passed")
        
        return test_results

def main():
    """Main function to run the tests"""
    BASE_URL = "http://localhost:8000"
    AUTH_TOKEN = "your_auth_token_here"
    
    if AUTH_TOKEN == "your_auth_token_here":
        logger.error("❌ Please update AUTH_TOKEN with your actual authentication token")
        return
    
    try:
        runner = CoreLocationTestRunner(BASE_URL, AUTH_TOKEN)
        results = runner.run_all_tests()
        
        print(f"\n📊 SUMMARY: {results['summary']['passed']}/{results['summary']['total']} tests passed")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"core_location_test_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Test runner failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
