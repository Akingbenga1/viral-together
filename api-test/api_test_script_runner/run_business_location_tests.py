#!/usr/bin/env python3
"""
Business Location Management Test Runner
Tests CRUD operations for business locations
"""

import requests
import json
import time
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BusinessLocationTestRunner:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        })
        self.created_location_ids = []
        
    def test_add_business_location(self, business_id: int, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test adding a location for a business"""
        url = f"{self.base_url}/api/v1/businesses/{business_id}/locations"
        
        logger.info(f"Testing add location for business {business_id}: {location_data['city_name']}")
        response = self.session.post(url, json=location_data)
        
        if response.status_code == 200:
            result = response.json()
            location_id = result.get('id')
            if location_id:
                self.created_location_ids.append(location_id)
            logger.info(f"✅ Location added successfully: ID {location_id}")
            return {"success": True, "data": result, "status_code": response.status_code, "location_id": location_id}
        else:
            logger.error(f"❌ Failed to add location: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_get_business_locations(self, business_id: int) -> Dict[str, Any]:
        """Test getting all locations for a business"""
        url = f"{self.base_url}/api/v1/businesses/{business_id}/locations"
        
        logger.info(f"Testing get locations for business {business_id}")
        response = self.session.get(url)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Retrieved {len(result)} locations")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Failed to get locations: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_update_business_location(self, location_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test updating a business location"""
        url = f"{self.base_url}/api/v1/businesses/locations/{location_id}"
        
        logger.info(f"Testing update location {location_id}")
        response = self.session.put(url, json=update_data)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Location updated successfully")
            return {"success": True, "data": result, "status_code": response.status_code}
        else:
            logger.error(f"❌ Failed to update location: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def test_delete_business_location(self, location_id: int) -> Dict[str, Any]:
        """Test deleting a business location"""
        url = f"{self.base_url}/api/v1/businesses/locations/{location_id}"
        
        logger.info(f"Testing delete location {location_id}")
        response = self.session.delete(url)
        
        if response.status_code == 200:
            logger.info(f"✅ Location deleted successfully")
            return {"success": True, "data": response.json(), "status_code": response.status_code}
        else:
            logger.error(f"❌ Failed to delete location: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text, "status_code": response.status_code}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all business location management tests"""
        logger.info("🚀 Starting Business Location Management Tests")
        
        test_results = {
            "add_tests": [],
            "get_tests": [],
            "update_tests": [],
            "delete_tests": [],
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
        
        # Test data for locations
        test_locations = [
            {
                "city_name": "San Francisco",
                "region_name": "California",
                "region_code": "CA",
                "country_code": "US",
                "country_name": "United States",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "postcode": "94102",
                "time_zone": "America/Los_Angeles",
                "is_primary": True
            },
            {
                "city_name": "Austin",
                "region_name": "Texas",
                "region_code": "TX",
                "country_code": "US",
                "country_name": "United States",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "postcode": "73301",
                "time_zone": "America/Chicago",
                "is_primary": False
            }
        ]
        
        # Test adding locations
        for i, location_data in enumerate(test_locations):
            result = self.test_add_business_location(1, location_data)
            test_results["add_tests"].append(result)
            time.sleep(0.5)  # Small delay between requests
        
        # Test getting locations
        result = self.test_get_business_locations(1)
        test_results["get_tests"].append(result)
        
        result = self.test_get_business_locations(2)
        test_results["get_tests"].append(result)
        
        # Test updating locations (if we have created locations)
        if self.created_location_ids:
            update_data = {
                "city_name": "San Francisco Updated",
                "country_code": "US",
                "country_name": "United States",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "is_primary": False
            }
            result = self.test_update_business_location(self.created_location_ids[0], update_data)
            test_results["update_tests"].append(result)
        
        # Test deleting locations (if we have created locations)
        if len(self.created_location_ids) > 1:
            result = self.test_delete_business_location(self.created_location_ids[1])
            test_results["delete_tests"].append(result)
        
        # Calculate summary
        all_tests = (test_results["add_tests"] + test_results["get_tests"] + 
                    test_results["update_tests"] + test_results["delete_tests"])
        
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
        runner = BusinessLocationTestRunner(BASE_URL, AUTH_TOKEN)
        results = runner.run_all_tests()
        
        print(f"\n📊 SUMMARY: {results['summary']['passed']}/{results['summary']['total']} tests passed")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"business_location_test_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Test runner failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
