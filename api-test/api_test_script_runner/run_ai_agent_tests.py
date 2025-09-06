#!/usr/bin/env python3
"""
Automated API Test Runner for AI Agent Endpoints
This script automatically tests all endpoints defined in ai_agent_tests.http
"""

import requests
import json
import time
import sys
import getpass
import urllib.parse
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    name: str
    method: str
    endpoint: str
    status_code: int
    response_time: float
    success: bool
    error: str = None
    response_data: Any = None

class AIAgentAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results: List[TestResult] = []
        
    def login(self) -> bool:
        """Login to get authentication token"""
        try:
            print("🔐 Logging in...")
            
            # Get database authentication credentials from user
            username = input("Enter database authentication username: ")
            password = getpass.getpass("Enter database authentication password: ")
            
            response = self.session.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                print(f"✅ Login successful - Token: {self.auth_token[:20]}...")
                return True
            else:
                print(f"❌ Login failed - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Login error: {e}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    expected_status: int = 200, use_form_data: bool = False) -> TestResult:
        """Make HTTP request and return test result"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if data and not use_form_data:
            headers["Content-Type"] = "application/json"
        
        start_time = time.time()
        
        try:
            if use_form_data:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,  # Use data instead of json for form data
                    timeout=30
                )
            else:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    timeout=30
                )
            
            response_time = time.time() - start_time
            success = response.status_code == expected_status
            
            # Try to parse JSON response
            try:
                response_data = response.json() if response.content else None
            except json.JSONDecodeError:
                response_data = response.text
            
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time=response_time,
                success=success,
                response_data=response_data
            )
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return TestResult(
                name=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=0,
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all AI agent API tests"""
        print("🚀 Starting AI Agent API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        self._run_test_1_create_ai_agent()
        self._run_test_2_get_all_ai_agents()
        self._run_test_3_get_specific_ai_agent()
        self._run_test_4_record_agent_response()
        self._run_test_5_get_agent_responses()
        self._run_test_6_get_task_responses()
        self._run_test_7_create_user_agent_association()
        self._run_test_8_get_user_agents()
        self._run_test_9_get_agent_users()
        self._run_test_9_5_get_user_primary_agent()
        self._run_test_10_create_coordination_session()
        self._run_test_11_get_available_agents()
        self._run_test_12_get_agent_context()
        self._run_test_13_store_user_conversation()
        self._run_test_14_retrieve_user_conversations()
        self._run_test_15_get_conversation_history()
        
        return self.test_results
        
        # Individual test methods will be defined below
    
    def _run_test_1_create_ai_agent(self):
        """Test 1: Create AI Agent"""
        print("\n1️⃣ Creating AI Agent...")
        create_agent_data = {
            "name": "Chat Support Agent",
            "agent_type": "chat_support",
            "capabilities": {
                "capabilities": ["chat", "customer_support", "faq"],
                "limitations": ["complex_technical_issues"]
            }
        }
        result = self.make_request("POST", "/ai-agents/", create_agent_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_2_get_all_ai_agents(self):
        """Test 2: Get All AI Agents"""
        print("\n2️⃣ Getting All AI Agents...")
        result = self.make_request("GET", "/ai-agents/")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_3_get_specific_ai_agent(self):
        """Test 3: Get Specific AI Agent"""
        print("\n3️⃣ Getting Specific AI Agent...")
        result = self.make_request("GET", "/ai-agents/1")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_4_record_agent_response(self):
        """Test 4: Record Agent Response"""
        print("\n4️⃣ Recording Agent Response...")
        response_data = {
            "agent_id": 1,
            "task_id": "task_123",
            "response": "I can help you with that question. Here's the information you need...",
            "response_type": "task_response"
        }
        result = self.make_request("POST", "/ai-agents/responses", response_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_5_get_agent_responses(self):
        """Test 5: Get Agent Responses"""
        print("\n5️⃣ Getting Agent Responses...")
        result = self.make_request("GET", "/ai-agents/responses/agent/1?limit=10")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_6_get_task_responses(self):
        """Test 6: Get Task Responses"""
        print("\n6️⃣ Getting Task Responses...")
        result = self.make_request("GET", "/ai-agents/responses/task/task_123")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_7_create_user_agent_association(self):
        """Test 7: Create User-Agent Association"""
        print("\n7️⃣ Creating User-Agent Association...")
        association_data = {
            "user_id": 1,
            "agent_id": 2,  # Use agent_id 2 instead of 1 to avoid duplicate
            "association_type": "secondary",
            "is_primary": False,  # Set to False to avoid unique constraint violation
            "priority": 2,
            "status": "active",
            "assigned_by": 1
        }
        result = self.make_request("POST", "/ai-agents/associations", association_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_8_get_user_agents(self):
        """Test 8: Get User's Agents"""
        print("\n8️⃣ Getting User's Agents...")
        result = self.make_request("GET", "/ai-agents/associations/user/1")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_get_agent_users(self):
        """Test 9: Get Agent's Users"""
        print("\n9️⃣ Getting Agent's Users...")
        result = self.make_request("GET", "/ai-agents/associations/agent/1")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_9_5_get_user_primary_agent(self):
        """Test 9.5: Get User's Primary Agent"""
        print("\n9️⃣5️⃣ Getting User's Primary Agent...")
        result = self.make_request("GET", "/ai-agents/associations/user/1/primary")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_10_create_coordination_session(self):
        """Test 10: Create Coordination Session"""
        print("\n🔟 Creating Coordination Session...")
        coordination_data = {
            "user_id": 1,
            "task_type": "customer_support",
            "initial_context": {
                "customer_issue": "Payment problem",
                "priority": "high"
            }
        }
        result = self.make_request("POST", "/ai-agents/coordination/sessions", coordination_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_11_get_available_agents(self):
        """Test 11: Get Available Agents"""
        print("\n1️⃣1️⃣ Getting Available Agents...")
        result = self.make_request("GET", "/ai-agents/coordination/agents/1?capability=chat_support")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_12_get_agent_context(self):
        """Test 12: Get Agent Context"""
        print("\n1️⃣2️⃣ Getting Agent Context...")
        context_data = {
            "user_id": 1,
            "current_prompt": "I need help with my payment",
            "agent_id": 1,
            "context_window": 10
        }
        result = self.make_request("POST", "/ai-agents/coordination/context", context_data)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_13_store_user_conversation(self):
        """Test 13: Store User Conversation"""
        print("\n1️⃣3️⃣ Storing User Conversation...")
        # The endpoint expects query parameters, not form data or JSON body
        conversation_text = "User: I need help with my payment\nAgent: I can help you with that. What specific issue are you experiencing?"
        # URL encode the conversation text to handle newlines and special characters
        encoded_text = urllib.parse.quote(conversation_text)
        url = f"/ai-agents/conversations?user_id=1&conversation_text={encoded_text}&conversation_type=customer_support"
        result = self.make_request("POST", url, None)  # No data body needed
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_14_retrieve_user_conversations(self):
        """Test 14: Retrieve User Conversations"""
        print("\n1️⃣4️⃣ Retrieving User Conversations...")
        result = self.make_request("GET", "/ai-agents/conversations/1?query=payment&limit=5&conversation_type=customer_support")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def _run_test_15_get_conversation_history(self):
        """Test 15: Get Conversation History"""
        print("\n1️⃣5️⃣ Getting Conversation History...")
        result = self.make_request("GET", "/ai-agents/conversations/1/history")
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
    
    def run_error_tests(self) -> List[TestResult]:
        """Run error case tests"""
        print("\n" + "=" * 60)
        print("🧪 Running Error Case Tests...")
        print("=" * 60)
        
        # Error Test 1: Create AI Agent with Invalid Data
        print("\n❌ Creating AI Agent with Invalid Data...")
        invalid_data = {
            "name": "",
            "agent_type": "invalid_type",
            "capabilities": {},
            "user_id": 999
        }
        result = self.make_request("POST", "/ai-agents/", invalid_data, expected_status=422)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 2: Get Non-existent Agent
        print("\n❌ Getting Non-existent Agent...")
        result = self.make_request("GET", "/ai-agents/999", expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        # Error Test 3: Record Response for Non-existent Agent
        print("\n❌ Recording Response for Non-existent Agent...")
        invalid_response_data = {
            "agent_id": 999,
            "task_id": "task_123",
            "response": "This should fail",
            "response_type": "task_response"
        }
        result = self.make_request("POST", "/ai-agents/responses", invalid_response_data, expected_status=404)
        self.test_results.append(result)
        print(f"   Status: {result.status_code} | Time: {result.response_time:.2f}s")
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.success:
                    print(f"   - {result.name}: {result.status_code} {result.error or ''}")
        
        # Calculate average response time
        avg_response_time = sum(result.response_time for result in self.test_results) / total_tests
        print(f"\n⏱️  Average Response Time: {avg_response_time:.2f}s")

def main():
    """Main function to run the tests"""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python run_ai_agent_tests.py [base_url] [test_number]")
        print("  python run_ai_agent_tests.py                    # Run all tests")
        print("  python run_ai_agent_tests.py http://localhost:8000  # Run all tests with custom URL")
        print("  python run_ai_agent_tests.py http://localhost:8000 8  # Run only test 8")
        print("\nAvailable test numbers:")
        print("  1  - Create AI Agent")
        print("  2  - Get All AI Agents")
        print("  3  - Get Specific AI Agent")
        print("  4  - Record Agent Response")
        print("  5  - Get Agent Responses")
        print("  6  - Get Task Responses")
        print("  7  - Create User-Agent Association")
        print("  8  - Get User's Agents")
        print("  9  - Get Agent's Users")
        print("  9.5- Get User's Primary Agent")
        print("  10 - Create Coordination Session")
        print("  11 - Get Available Agents")
        print("  12 - Get Agent Context")
        print("  13 - Store User Conversation")
        print("  14 - Retrieve User Conversations")
        print("  15 - Get Conversation History")
        sys.exit(1)
    
    # Parse arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_number = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = AIAgentAPITester(base_url)
    
    # Login first
    if not tester.login():
        print("❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Run specific test or all tests
    if test_number:
        print(f"🧪 Running Test {test_number} only...")
        print(f"📍 Base URL: {base_url}")
        print("=" * 60)
        
        # Map test numbers to methods
        test_methods = {
            "1": tester._run_test_1_create_ai_agent,
            "2": tester._run_test_2_get_all_ai_agents,
            "3": tester._run_test_3_get_specific_ai_agent,
            "4": tester._run_test_4_record_agent_response,
            "5": tester._run_test_5_get_agent_responses,
            "6": tester._run_test_6_get_task_responses,
            "7": tester._run_test_7_create_user_agent_association,
            "8": tester._run_test_8_get_user_agents,
            "9": tester._run_test_9_get_agent_users,
            "9.5": tester._run_test_9_5_get_user_primary_agent,
            "10": tester._run_test_10_create_coordination_session,
            "11": tester._run_test_11_get_available_agents,
            "12": tester._run_test_12_get_agent_context,
            "13": tester._run_test_13_store_user_conversation,
            "14": tester._run_test_14_retrieve_user_conversations,
            "15": tester._run_test_15_get_conversation_history,
        }
        
        if test_number in test_methods:
            test_methods[test_number]()
        else:
            print(f"❌ Invalid test number: {test_number}")
            print("Available test numbers: 1, 2, 3, 4, 5, 6, 7, 8, 9, 9.5, 10, 11, 12, 13, 14, 15")
            sys.exit(1)
    else:
        # Run all tests
        tester.run_all_tests()
        # Run error tests
        tester.run_error_tests()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()
