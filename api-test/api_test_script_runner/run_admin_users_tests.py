#!/usr/bin/env python3
"""
Admin Users Management API Test Script

This script tests the admin user management endpoints:
- GET /admin/users - List all users
- GET /admin/users/{user_id}/profile - Get specific user profile
- PUT /admin/users/{user_id}/profile_update - Update user profile
- PUT /admin/users/{user_id}/password_update - Update user password

Usage:
    python run_admin_users_tests.py

Requirements:
    - Valid admin or super_admin access token for authentication
    - API server running on localhost:8000
"""

import requests
import json
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdminUsersAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        
    def set_auth_token(self, token: str):
        """Set the authentication token for API requests"""
        self.access_token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Make an API request and return the response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"API REQUEST: {method} {endpoint}")
            if data:
                logger.info(f"REQUEST DATA: {json.dumps(data, indent=2)}")
            
            response = self.session.request(method, url, json=data)
            
            logger.info(f"RESPONSE STATUS: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"RESPONSE DATA: {json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
                logger.info(f"RAW RESPONSE: {response.text}")
            
            if response.status_code != expected_status:
                logger.warning(f"Expected status {expected_status}, got {response.status_code}")
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": response.status_code == expected_status
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
    
    def test_list_users(self) -> Dict[str, Any]:
        """Test listing all users"""
        logger.info("=" * 50)
        logger.info("TEST: List All Users")
        logger.info("=" * 50)
        
        return self.make_request("GET", "/admin/users")
    
    def test_get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Test getting specific user profile"""
        logger.info("=" * 50)
        logger.info(f"TEST: Get User Profile for User ID {user_id}")
        logger.info("=" * 50)
        
        return self.make_request("GET", f"/admin/users/{user_id}/profile")
    
    def test_update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test updating user profile"""
        logger.info("=" * 50)
        logger.info(f"TEST: Update User Profile for User ID {user_id}")
        logger.info("=" * 50)
        
        return self.make_request("PUT", f"/admin/users/{user_id}/profile_update", profile_data)
    
    def test_update_user_profile_with_password(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test updating user profile with password"""
        logger.info("=" * 50)
        logger.info(f"TEST: Update User Profile with Password for User ID {user_id}")
        logger.info("=" * 50)
        
        return self.make_request("PUT", f"/admin/users/{user_id}/profile_update", profile_data)
    
    def test_validation_errors(self, user_id: int) -> Dict[str, Any]:
        """Test various validation error scenarios"""
        logger.info("=" * 50)
        logger.info("TEST: Validation Errors")
        logger.info("=" * 50)
        
        results = {}
        
        # Test invalid email
        logger.info("Testing invalid email format...")
        results["invalid_email"] = self.make_request(
            "PUT", 
            f"/admin/users/{user_id}/profile_update", 
            {"email": "invalid-email-format"},
            expected_status=422
        )
        
        # Test weak password
        logger.info("Testing weak password...")
        results["weak_password"] = self.make_request(
            "PUT",
            f"/admin/users/{user_id}/profile_update",
            {
                "new_password": "weak",
                "confirm_password": "weak"
            },
            expected_status=422
        )
        
        # Test password mismatch
        logger.info("Testing password mismatch...")
        results["password_mismatch"] = self.make_request(
            "PUT",
            f"/admin/users/{user_id}/profile_update",
            {
                "new_password": "NewPassword123",
                "confirm_password": "DifferentPassword123"
            },
            expected_status=422
        )
        
        # Test empty username
        logger.info("Testing empty username...")
        results["empty_username"] = self.make_request(
            "PUT",
            f"/admin/users/{user_id}/profile_update",
            {"username": ""},
            expected_status=422
        )
        
        return results
    
    def test_authorization_errors(self, user_id: int) -> Dict[str, Any]:
        """Test authorization error scenarios"""
        logger.info("=" * 50)
        logger.info("TEST: Authorization Errors")
        logger.info("=" * 50)
        
        results = {}
        
        # Test without authentication
        logger.info("Testing without authentication...")
        original_headers = self.session.headers.copy()
        del self.session.headers['Authorization']
        
        results["no_auth"] = self.make_request(
            "PUT",
            f"/admin/users/{user_id}/profile_update",
            {"first_name": "Test"},
            expected_status=401
        )
        
        # Restore headers
        self.session.headers = original_headers
        
        # Test with invalid token
        logger.info("Testing with invalid token...")
        self.session.headers['Authorization'] = 'Bearer invalid_token_here'
        
        results["invalid_token"] = self.make_request(
            "PUT",
            f"/admin/users/{user_id}/profile_update",
            {"first_name": "Test"},
            expected_status=401
        )
        
        # Restore original token
        self.session.headers['Authorization'] = f'Bearer {self.access_token}'
        
        return results
    
    def test_not_found_errors(self) -> Dict[str, Any]:
        """Test not found error scenarios"""
        logger.info("=" * 50)
        logger.info("TEST: Not Found Errors")
        logger.info("=" * 50)
        
        results = {}
        non_existent_user_id = 99999
        
        # Test getting non-existent user profile
        logger.info("Testing get non-existent user profile...")
        results["get_nonexistent"] = self.make_request(
            "GET",
            f"/admin/users/{non_existent_user_id}/profile",
            expected_status=404
        )
        
        # Test updating non-existent user profile
        logger.info("Testing update non-existent user profile...")
        results["update_nonexistent"] = self.make_request(
            "PUT",
            f"/admin/users/{non_existent_user_id}/profile_update",
            {"first_name": "Test"},
            expected_status=404
        )
        
        # Test updating profile with password for non-existent user
        logger.info("Testing update profile with password for non-existent user...")
        results["password_nonexistent"] = self.make_request(
            "PUT",
            f"/admin/users/{non_existent_user_id}/profile_update",
            {
                "first_name": "Test",
                "new_password": "NewPassword123",
                "confirm_password": "NewPassword123"
            },
            expected_status=404
        )
        
        return results
    
    def run_all_tests(self, test_user_id: int = 1):
        """Run all admin users tests"""
        if not self.access_token:
            logger.error("No access token provided. Please set authentication token first.")
            return
        
        logger.info("Starting Admin Users API Tests...")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Access Token: {self.access_token[:20]}...")
        logger.info(f"Test User ID: {test_user_id}")
        
        # Test 1: List all users
        list_result = self.test_list_users()
        
        # Test 2: Get specific user profile
        profile_result = self.test_get_user_profile(test_user_id)
        
        # Test 3: Update user profile with valid data
        update_data = {
            "first_name": "Admin Test",
            "last_name": "User",
            "email": f"admin.test.user.{test_user_id}@example.com",
            "mobile_number": "+1234567890",
            "username": f"admintestuser{test_user_id}"
        }
        update_result = self.test_update_user_profile(test_user_id, update_data)
        
        # Test 4: Update profile with password
        password_data = {
            "first_name": "Admin Test",
            "new_password": "AdminPassword123",
            "confirm_password": "AdminPassword123"
        }
        password_result = self.test_update_user_profile_with_password(test_user_id, password_data)
        
        # Test 5: Validation errors
        validation_results = self.test_validation_errors(test_user_id)
        
        # Test 6: Authorization errors
        auth_results = self.test_authorization_errors(test_user_id)
        
        # Test 7: Not found errors
        not_found_results = self.test_not_found_errors()
        
        # Summary
        logger.info("=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"List Users: {'PASS' if list_result['success'] else 'FAIL'}")
        logger.info(f"Get Profile: {'PASS' if profile_result['success'] else 'FAIL'}")
        logger.info(f"Update Profile: {'PASS' if update_result['success'] else 'FAIL'}")
        logger.info(f"Update Password: {'PASS' if password_result['success'] else 'FAIL'}")
        
        validation_passed = all(result['success'] for result in validation_results.values())
        logger.info(f"Validation Tests: {'PASS' if validation_passed else 'FAIL'}")
        
        auth_passed = all(result['success'] for result in auth_results.values())
        logger.info(f"Authorization Tests: {'PASS' if auth_passed else 'FAIL'}")
        
        not_found_passed = all(result['success'] for result in not_found_results.values())
        logger.info(f"Not Found Tests: {'PASS' if not_found_passed else 'FAIL'}")
        
        return {
            "list_test": list_result,
            "profile_test": profile_result,
            "update_test": update_result,
            "password_test": password_result,
            "validation_tests": validation_results,
            "authorization_tests": auth_results,
            "not_found_tests": not_found_results
        }

def main():
    """Main function to run the tests"""
    print("Admin Users Management API Test Script")
    print("=" * 50)
    
    # Get access token from user
    access_token = input("Enter your admin/super_admin access token: ").strip()
    if not access_token:
        print("Error: Access token is required")
        sys.exit(1)
    
    # Get test user ID
    test_user_id = input("Enter user ID to test with (default: 1): ").strip()
    if not test_user_id:
        test_user_id = 1
    else:
        try:
            test_user_id = int(test_user_id)
        except ValueError:
            print("Error: User ID must be a number")
            sys.exit(1)
    
    # Initialize tester
    tester = AdminUsersAPITester()
    tester.set_auth_token(access_token)
    
    # Run tests
    try:
        results = tester.run_all_tests(test_user_id)
        print("\nTests completed successfully!")
        
        # Check if all tests passed
        all_passed = (
            results["list_test"]["success"] and
            results["profile_test"]["success"] and
            results["update_test"]["success"] and
            results["password_test"]["success"] and
            all(result["success"] for result in results["validation_tests"].values()) and
            all(result["success"] for result in results["authorization_tests"].values()) and
            all(result["success"] for result in results["not_found_tests"].values())
        )
        
        if all_passed:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. Check the logs above for details.")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
