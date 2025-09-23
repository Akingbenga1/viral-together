# 🚀 API Endpoints Quick Reference Guide

## 📊 **Real-time Analytics Endpoints** (`/api/analytics/`)

| # | Method | Endpoint | Description | Test File |
|---|--------|----------|-------------|-----------|
| 1 | GET | `/api/analytics/engagement-trends/{user_id}` | Get engagement trends for a user | `real_time_analytics_tests.http` |
| 2 | GET | `/api/analytics/market-rates` | Get current market rates for content | `real_time_analytics_tests.http` |
| 3 | GET | `/api/analytics/competitor-analysis/{user_id}` | Get competitor analysis | `real_time_analytics_tests.http` |
| 4 | GET | `/api/analytics/trending-content` | Get trending content for a platform | `real_time_analytics_tests.http` |
| 5 | GET | `/api/analytics/live-metrics/{user_id}` | Get live metrics for a user | `real_time_analytics_tests.http` |
| 6 | GET | `/api/analytics/trending-topics` | Get trending topics for a platform | `real_time_analytics_tests.http` |
| 7 | GET | `/api/analytics/market-insights` | Get market insights for an industry | `real_time_analytics_tests.http` |
| 8 | GET | `/api/analytics/analytics-summary/{user_id}` | Get comprehensive analytics summary | `real_time_analytics_tests.http` |

### Example Usage:
```bash
# Get engagement trends for user 1
curl "http://localhost:8000/api/analytics/engagement-trends/1?days=30"

# Get market rates for Instagram sponsored posts
curl "http://localhost:8000/api/analytics/market-rates?platform=instagram&content_type=sponsored_post"

# Get trending content for TikTok
curl "http://localhost:8000/api/analytics/trending-content?platform=tiktok&limit=20"
```

---

## 💼 **Influencer Marketing Endpoints** (`/api/influencer-marketing/`)

| # | Method | Endpoint | Description | Test File |
|---|--------|----------|-------------|-----------|
| 9 | GET | `/api/influencer-marketing/brand-opportunities/{user_id}` | Get brand partnership opportunities | `influencer_marketing_tests.http` |
| 10 | GET | `/api/influencer-marketing/content-recommendations/{user_id}` | Get content recommendations based on trends | `influencer_marketing_tests.http` |
| 11 | GET | `/api/influencer-marketing/pricing-recommendations/{user_id}` | Get pricing recommendations based on market analysis | `influencer_marketing_tests.http` |
| 12 | GET | `/api/influencer-marketing/growth-strategies/{user_id}` | Get growth strategies based on current trends | `influencer_marketing_tests.http` |
| 13 | GET | `/api/influencer-marketing/marketing-insights/{user_id}` | Get comprehensive marketing insights | `influencer_marketing_tests.http` |
| 14 | GET | `/api/influencer-marketing/trending-hashtags` | Get trending hashtags for a platform | `influencer_marketing_tests.http` |
| 15 | GET | `/api/influencer-marketing/market-insights` | Get market insights for an industry | `influencer_marketing_tests.http` |
| 16 | GET | `/api/influencer-marketing/opportunity-alerts/{user_id}` | Get opportunity alerts for a user | `influencer_marketing_tests.http` |

### Example Usage:
```bash
# Get brand opportunities for user 1
curl "http://localhost:8000/api/influencer-marketing/brand-opportunities/1?limit=20"

# Get content recommendations for Instagram
curl "http://localhost:8000/api/influencer-marketing/content-recommendations/1?platform=instagram&limit=15"

# Get pricing recommendations
curl "http://localhost:8000/api/influencer-marketing/pricing-recommendations/1"
```

---

## 🤖 **Enhanced AI Agents Endpoints** (`/api/enhanced-ai-agents/`)

| # | Method | Endpoint | Description | Test File |
|---|--------|----------|-------------|-----------|
| 17 | GET | `/api/enhanced-ai-agents/agent-capabilities` | Get AI agent capabilities and real-time data integration status | `enhanced_ai_agents_tests.http` |
| 18 | GET | `/api/enhanced-ai-agents/data-sources/status` | Get status of real-time data sources | `enhanced_ai_agents_tests.http` |
| 19 | GET | `/api/enhanced-ai-agents/enhanced-recommendations/{user_id}` | Get enhanced recommendations with real-time data | `enhanced_ai_agents_tests.http` |
| 20 | POST | `/api/enhanced-ai-agents/execute-with-real-time-data` | Execute AI agent with real-time data integration | `enhanced_ai_agents_tests.http` |
| 21 | POST | `/api/enhanced-ai-agents/batch-recommendations` | Get recommendations from multiple AI agents in batch | `enhanced_ai_agents_tests.http` |
| 22 | GET | `/api/enhanced-ai-agents/recommendation-history/{user_id}` | Get recommendation history for a user | `enhanced_ai_agents_tests.http` |

### Example Usage:
```bash
# Get all agent capabilities
curl "http://localhost:8000/api/enhanced-ai-agents/agent-capabilities"

# Get growth advisor recommendations
curl "http://localhost:8000/api/enhanced-ai-agents/enhanced-recommendations/1?agent_type=growth_advisor"

# Execute agent with real-time data
curl -X POST "http://localhost:8000/api/enhanced-ai-agents/execute-with-real-time-data" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "prompt": "Provide growth strategies for my influencer account",
    "context": {"agent_type": "growth_advisor", "user_id": 1},
    "real_time_data": {"trending_content": []}
  }'
```

---

## 🧪 **Test Files Available**

### Individual Test Files:
1. **`real_time_analytics_tests.http`** - 20 tests for analytics endpoints
2. **`influencer_marketing_tests.http`** - 24 tests for influencer marketing endpoints  
3. **`enhanced_ai_agents_tests.http`** - 10 tests for AI agent endpoints

### Comprehensive Test File:
4. **`comprehensive_new_features_tests.http`** - 67 tests covering all new features

---

## 🚀 **Quick Start Testing**

### 1. Test Real-time Analytics:
```bash
# Open in VS Code or REST Client
viral-together/api-test/api_endpoint_test/real_time_analytics_tests.http
```

### 2. Test Influencer Marketing:
```bash
# Open in VS Code or REST Client
viral-together/api-test/api_endpoint_test/influencer_marketing_tests.http
```

### 3. Test Enhanced AI Agents:
```bash
# Open in VS Code or REST Client
viral-together/api-test/api_endpoint_test/enhanced_ai_agents_tests.http
```

### 4. Test Everything at Once:
```bash
# Open in VS Code or REST Client
viral-together/api-test/api_endpoint_test/comprehensive_new_features_tests.http
```

---

## 🐍 **Python Test Runners**

### Run Individual Test Suites:
```bash
# Test enhanced AI agents
python api-test/api_test_script_runner/test_enhanced_ai_agents.py

# Test all real-time services
python api-test/api_test_script_runner/test_real_time_services.py
```

---

## 📋 **Available Agent Types**

When testing AI agents, you can use these agent types:

1. **`growth_advisor`** - Audience growth strategies
2. **`business_advisor`** - Business development and monetization
3. **`content_advisor`** - Content strategy and creation
4. **`analytics_advisor`** - Performance analysis and insights
5. **`collaboration_advisor`** - Brand partnerships and collaborations
6. **`pricing_advisor`** - Pricing optimization and market analysis
7. **`platform_advisor`** - Platform-specific strategies
8. **`engagement_advisor`** - Audience engagement optimization
9. **`optimization_advisor`** - Performance optimization

---

## 🌐 **Supported Platforms**

When testing platform-specific endpoints, you can use:

1. **`instagram`** - Instagram platform
2. **`tiktok`** - TikTok platform
3. **`youtube`** - YouTube platform
4. **`twitter`** - Twitter platform

---

## 📊 **Response Examples**

### Analytics Response:
```json
{
  "user_id": 1,
  "days_analyzed": 30,
  "engagement_trends": [
    {
      "platform": "instagram",
      "followers": 50000,
      "engagement_rate": 4.2,
      "reach": 45000,
      "impressions": 50000,
      "timestamp": "2024-12-01T12:00:00Z"
    }
  ],
  "summary": {
    "total_platforms": 1,
    "average_engagement_rate": 4.2,
    "total_followers": 50000,
    "last_updated": "2024-12-01T12:00:00Z"
  }
}
```

### AI Agent Response:
```json
{
  "agent_id": 1,
  "agent_type": "growth_advisor",
  "focus_area": "audience_growth",
  "response": "Based on current trends, I recommend focusing on...",
  "status": "success",
  "real_time_data_used": {
    "data_types": ["trending_content", "engagement_trends"],
    "data_freshness": "real-time",
    "timestamp": "2024-12-01T12:00:00Z"
  }
}
```

---

## ⚡ **Performance Notes**

- All endpoints include caching (5-minute TTL by default)
- Rate limiting is built-in for all external APIs
- Concurrent requests are supported
- Error handling with graceful degradation
- Real-time data freshness indicators

---

## 🔧 **Configuration**

Make sure these environment variables are set:

```bash
ENHANCED_AI_AGENTS_ENABLED=true
WEB_SEARCH_ENABLED=true
AI_AGENT_TOOL_CALLING_ENABLED=true
AI_AGENT_MCP_ENABLED=true
```

For full configuration, see `ENHANCED_AI_AGENTS_README.md`
