#!/usr/bin/env python3
"""
Enhanced AI Agents API Test Runner
Tests the new enhanced AI agents with real-time data integration
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_ai_agents_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedAIAgentsTester:
    """Test runner for Enhanced AI Agents API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_test(self, test_name: str, method: str, endpoint: str, 
                      data: Dict[str, Any] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Run a single test"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=data) as response:
                    result = await response.json()
                    status = response.status
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
                    status = response.status
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            success = status == expected_status
            test_result = {
                "test_name": test_name,
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "expected_status": expected_status,
                "success": success,
                "response": result,
                "timestamp": datetime.now().isoformat()
            }
            
            if success:
                logger.info(f"✅ {test_name} - PASSED")
            else:
                logger.error(f"❌ {test_name} - FAILED (Status: {status}, Expected: {expected_status})")
            
            self.test_results.append(test_result)
            return test_result
            
        except Exception as e:
            test_result = {
                "test_name": test_name,
                "method": method,
                "endpoint": endpoint,
                "status": None,
                "expected_status": expected_status,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.error(f"❌ {test_name} - ERROR: {str(e)}")
            self.test_results.append(test_result)
            return test_result
    
    async def test_agent_capabilities(self):
        """Test agent capabilities endpoints"""
        logger.info("🧪 Testing Agent Capabilities...")
        
        # Test 1: Get all agent capabilities
        await self.run_test(
            "Get All Agent Capabilities",
            "GET",
            "/api/enhanced-ai-agents/agent-capabilities"
        )
        
        # Test 2: Get specific agent capabilities
        await self.run_test(
            "Get Growth Advisor Capabilities",
            "GET",
            "/api/enhanced-ai-agents/agent-capabilities",
            {"agent_type": "growth_advisor"}
        )
        
        # Test 3: Get data sources status
        await self.run_test(
            "Get Data Sources Status",
            "GET",
            "/api/enhanced-ai-agents/data-sources/status"
        )
    
    async def test_enhanced_recommendations(self):
        """Test enhanced recommendations endpoints"""
        logger.info("🧪 Testing Enhanced Recommendations...")
        
        # Test different agent types
        agent_types = [
            "growth_advisor",
            "business_advisor",
            "content_advisor",
            "analytics_advisor",
            "collaboration_advisor",
            "pricing_advisor",
            "platform_advisor",
            "engagement_advisor",
            "optimization_advisor"
        ]
        
        for agent_type in agent_types:
            await self.run_test(
                f"Get {agent_type} Recommendations",
                "GET",
                f"/api/enhanced-ai-agents/enhanced-recommendations/1",
                {"agent_type": agent_type}
            )
    
    async def test_execute_with_real_time_data(self):
        """Test execute with real-time data endpoint"""
        logger.info("🧪 Testing Execute with Real-time Data...")
        
        test_data = {
            "agent_id": 1,
            "prompt": "Provide growth strategies for my influencer account",
            "context": {
                "agent_type": "growth_advisor",
                "user_id": 1
            },
            "real_time_data": {
                "trending_content": [
                    {
                        "platform": "instagram",
                        "hashtag": "#fashion",
                        "post_count": 1000,
                        "engagement_rate": 5.5,
                        "trend_score": 0.8
                    }
                ],
                "engagement_trends": [
                    {
                        "platform": "instagram",
                        "followers": 50000,
                        "engagement_rate": 4.2,
                        "reach": 45000,
                        "impressions": 50000
                    }
                ]
            }
        }
        
        await self.run_test(
            "Execute Agent with Real-time Data",
            "POST",
            "/api/enhanced-ai-agents/execute-with-real-time-data",
            test_data
        )
    
    async def test_batch_recommendations(self):
        """Test batch recommendations endpoint"""
        logger.info("🧪 Testing Batch Recommendations...")
        
        batch_data = {
            "user_id": 1,
            "agent_types": ["growth_advisor", "content_advisor", "pricing_advisor"],
            "real_time_context": {
                "platform": "instagram",
                "niche": "lifestyle"
            }
        }
        
        await self.run_test(
            "Get Batch Recommendations",
            "POST",
            "/api/enhanced-ai-agents/batch-recommendations",
            batch_data
        )
    
    async def test_recommendation_history(self):
        """Test recommendation history endpoint"""
        logger.info("🧪 Testing Recommendation History...")
        
        await self.run_test(
            "Get Recommendation History",
            "GET",
            "/api/enhanced-ai-agents/recommendation-history/1"
        )
        
        await self.run_test(
            "Get Recommendation History with Filters",
            "GET",
            "/api/enhanced-ai-agents/recommendation-history/1",
            {"agent_type": "growth_advisor", "limit": 5}
        )
    
    async def test_error_handling(self):
        """Test error handling"""
        logger.info("🧪 Testing Error Handling...")
        
        # Test invalid agent type
        await self.run_test(
            "Invalid Agent Type",
            "GET",
            "/api/enhanced-ai-agents/enhanced-recommendations/1",
            {"agent_type": "invalid_agent"},
            expected_status=400
        )
        
        # Test missing required parameters
        await self.run_test(
            "Missing Required Parameters",
            "POST",
            "/api/enhanced-ai-agents/execute-with-real-time-data",
            {"agent_id": 1},  # Missing prompt
            expected_status=400
        )
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Enhanced AI Agents API Tests...")
        start_time = datetime.now()
        
        try:
            await self.test_agent_capabilities()
            await self.test_enhanced_recommendations()
            await self.test_execute_with_real_time_data()
            await self.test_batch_recommendations()
            await self.test_recommendation_history()
            await self.test_error_handling()
            
        except Exception as e:
            logger.error(f"Test suite failed: {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("=" * 60)
        
        # Save detailed results
        with open(f"enhanced_ai_agents_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "duration": duration
        }

async def main():
    """Main function"""
    async with EnhancedAIAgentsTester() as tester:
        results = await tester.run_all_tests()
        
        # Exit with appropriate code
        if results["failed_tests"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
