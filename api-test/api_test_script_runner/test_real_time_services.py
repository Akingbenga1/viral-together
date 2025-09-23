#!/usr/bin/env python3
"""
Real-time Services API Test Runner
Tests all the new real-time services including analytics, influencer marketing, and enhanced AI agents
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
        logging.FileHandler('real_time_services_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealTimeServicesTester:
    """Test runner for Real-time Services API"""
    
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
    
    async def test_real_time_analytics(self):
        """Test real-time analytics endpoints"""
        logger.info("🧪 Testing Real-time Analytics...")
        
        # Test engagement trends
        await self.run_test(
            "Get Engagement Trends",
            "GET",
            "/api/analytics/engagement-trends/1",
            {"days": 30}
        )
        
        # Test market rates
        await self.run_test(
            "Get Market Rates - Instagram",
            "GET",
            "/api/analytics/market-rates",
            {"platform": "instagram", "content_type": "sponsored_post"}
        )
        
        # Test competitor analysis
        await self.run_test(
            "Get Competitor Analysis",
            "GET",
            "/api/analytics/competitor-analysis/1",
            {"competitors": ["competitor1", "competitor2"]}
        )
        
        # Test trending content
        await self.run_test(
            "Get Trending Content - Instagram",
            "GET",
            "/api/analytics/trending-content",
            {"platform": "instagram", "limit": 20}
        )
        
        # Test live metrics
        await self.run_test(
            "Get Live Metrics",
            "GET",
            "/api/analytics/live-metrics/1"
        )
        
        # Test analytics summary
        await self.run_test(
            "Get Analytics Summary",
            "GET",
            "/api/analytics/analytics-summary/1",
            {"days": 30}
        )
    
    async def test_influencer_marketing(self):
        """Test influencer marketing endpoints"""
        logger.info("🧪 Testing Influencer Marketing...")
        
        # Test brand opportunities
        await self.run_test(
            "Get Brand Opportunities",
            "GET",
            "/api/influencer-marketing/brand-opportunities/1",
            {"limit": 20}
        )
        
        # Test content recommendations
        await self.run_test(
            "Get Content Recommendations - Instagram",
            "GET",
            "/api/influencer-marketing/content-recommendations/1",
            {"platform": "instagram", "limit": 15}
        )
        
        # Test pricing recommendations
        await self.run_test(
            "Get Pricing Recommendations",
            "GET",
            "/api/influencer-marketing/pricing-recommendations/1"
        )
        
        # Test growth strategies
        await self.run_test(
            "Get Growth Strategies",
            "GET",
            "/api/influencer-marketing/growth-strategies/1",
            {"limit": 10}
        )
        
        # Test marketing insights
        await self.run_test(
            "Get Marketing Insights",
            "GET",
            "/api/influencer-marketing/marketing-insights/1"
        )
        
        # Test trending hashtags
        await self.run_test(
            "Get Trending Hashtags - Instagram",
            "GET",
            "/api/influencer-marketing/trending-hashtags",
            {"platform": "instagram", "limit": 20}
        )
        
        # Test opportunity alerts
        await self.run_test(
            "Get Opportunity Alerts",
            "GET",
            "/api/influencer-marketing/opportunity-alerts/1"
        )
    
    async def test_enhanced_ai_agents(self):
        """Test enhanced AI agents endpoints"""
        logger.info("🧪 Testing Enhanced AI Agents...")
        
        # Test agent capabilities
        await self.run_test(
            "Get Agent Capabilities",
            "GET",
            "/api/enhanced-ai-agents/agent-capabilities"
        )
        
        # Test data sources status
        await self.run_test(
            "Get Data Sources Status",
            "GET",
            "/api/enhanced-ai-agents/data-sources/status"
        )
        
        # Test enhanced recommendations
        await self.run_test(
            "Get Enhanced Recommendations - Growth Advisor",
            "GET",
            "/api/enhanced-ai-agents/enhanced-recommendations/1",
            {"agent_type": "growth_advisor"}
        )
        
        # Test execute with real-time data
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
                ]
            }
        }
        
        await self.run_test(
            "Execute Agent with Real-time Data",
            "POST",
            "/api/enhanced-ai-agents/execute-with-real-time-data",
            test_data
        )
        
        # Test batch recommendations
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
    
    async def test_cross_service_integration(self):
        """Test cross-service integration"""
        logger.info("🧪 Testing Cross-Service Integration...")
        
        # Test that analytics data can be used by AI agents
        await self.run_test(
            "Analytics to AI Agent Integration",
            "GET",
            "/api/enhanced-ai-agents/enhanced-recommendations/1",
            {"agent_type": "analytics_advisor"}
        )
        
        # Test that influencer marketing data can be used by AI agents
        await self.run_test(
            "Influencer Marketing to AI Agent Integration",
            "GET",
            "/api/enhanced-ai-agents/enhanced-recommendations/1",
            {"agent_type": "business_advisor"}
        )
    
    async def test_performance(self):
        """Test performance of real-time services"""
        logger.info("🧪 Testing Performance...")
        
        # Test concurrent requests
        tasks = []
        for i in range(5):
            task = self.run_test(
                f"Concurrent Request {i+1}",
                "GET",
                "/api/analytics/live-metrics/1"
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def test_error_handling(self):
        """Test error handling across all services"""
        logger.info("🧪 Testing Error Handling...")
        
        # Test invalid user ID
        await self.run_test(
            "Invalid User ID - Analytics",
            "GET",
            "/api/analytics/engagement-trends/999999",
            expected_status=500
        )
        
        # Test invalid platform
        await self.run_test(
            "Invalid Platform - Analytics",
            "GET",
            "/api/analytics/market-rates",
            {"platform": "invalid_platform", "content_type": "sponsored_post"},
            expected_status=500
        )
        
        # Test invalid agent type
        await self.run_test(
            "Invalid Agent Type - AI Agents",
            "GET",
            "/api/enhanced-ai-agents/enhanced-recommendations/1",
            {"agent_type": "invalid_agent"},
            expected_status=500
        )
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Real-time Services API Tests...")
        start_time = datetime.now()
        
        try:
            await self.test_real_time_analytics()
            await self.test_influencer_marketing()
            await self.test_enhanced_ai_agents()
            await self.test_cross_service_integration()
            await self.test_performance()
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
        with open(f"real_time_services_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
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
    async with RealTimeServicesTester() as tester:
        results = await tester.run_all_tests()
        
        # Exit with appropriate code
        if results["failed_tests"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
