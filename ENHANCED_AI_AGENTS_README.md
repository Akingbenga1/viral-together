# Enhanced AI Agents with Real-time Data Integration

## Overview

This document describes the enhanced AI agent system that provides real-time data integration, web search capabilities, social media API connections, and comprehensive influencer marketing insights. The system follows SOLID principles with proper interfaces for interchangeability and maintainability.

## Architecture

### Core Interfaces (`app/core/interfaces.py`)

The system is built around well-defined interfaces that ensure interchangeability:

- **IWebSearchService**: Interface for web search providers
- **ISocialMediaAPIService**: Interface for social media platform APIs
- **IAnalyticsService**: Interface for analytics and metrics services
- **IInfluencerMarketingService**: Interface for influencer marketing services
- **IRealTimeDataService**: Interface for real-time data services
- **IAIAgentService**: Interface for AI agent services
- **IDataProvider**: Interface for data providers (APIs, databases, etc.)

### Service Structure

```
app/services/
├── web_search/                 # Web search services
│   ├── base_web_search.py     # Base implementation
│   ├── duckduckgo_search.py   # DuckDuckGo implementation
│   ├── google_search.py       # Google Custom Search implementation
│   └── web_search_factory.py  # Factory for creating search services
├── social_media/              # Social media API services
│   ├── base_social_media.py   # Base implementation
│   ├── twitter_api.py         # Twitter API implementation
│   ├── instagram_api.py       # Instagram API implementation
│   ├── youtube_api.py         # YouTube API implementation
│   ├── tiktok_api.py          # TikTok API implementation
│   └── social_media_factory.py # Factory for creating social media services
├── analytics/                 # Analytics services
│   └── real_time_analytics.py # Real-time analytics implementation
├── influencer_marketing/      # Influencer marketing services
│   └── influencer_marketing_service.py # Main influencer marketing service
└── enhanced_ai_agent_service.py # Enhanced AI agent service
```

## Features

### 1. Real-time Web Search
- **DuckDuckGo Search**: Free, no API key required
- **Google Custom Search**: Requires API key and search engine ID
- **Trending Content Search**: Find trending topics and hashtags
- **News Search**: Get recent news and updates

### 2. Social Media API Integration
- **Twitter API v2**: User metrics, trending hashtags, post analytics
- **Instagram Basic Display API**: User metrics, media insights
- **YouTube Data API v3**: Channel statistics, video analytics, trending content
- **TikTok for Business API**: User metrics, video analytics, trending hashtags

### 3. Real-time Analytics
- **Engagement Tracking**: Live engagement metrics and trends
- **Market Analysis**: Current market rates and pricing data
- **Competitor Analysis**: Real-time competitor benchmarking
- **Trending Content**: Platform-specific trending content identification

### 4. Influencer Marketing Services
- **Brand Partnership Opportunities**: Real-time brand opportunity discovery
- **Content Recommendations**: AI-powered content suggestions based on trends
- **Pricing Recommendations**: Market-based pricing optimization
- **Growth Strategies**: Data-driven growth recommendations

### 5. Enhanced AI Agents
- **Real-time Data Integration**: Agents use live data for recommendations
- **Multi-agent Coordination**: Agents work together with specialized roles
- **Context-aware Responses**: Responses based on current market conditions
- **Performance Tracking**: Monitor agent performance and data quality

## API Endpoints

### Real-time Analytics (`/api/analytics/`)
- `GET /engagement-trends/{user_id}` - Get engagement trends
- `GET /market-rates` - Get current market rates
- `GET /competitor-analysis/{user_id}` - Get competitor analysis
- `GET /trending-content` - Get trending content
- `GET /live-metrics/{user_id}` - Get live metrics
- `GET /analytics-summary/{user_id}` - Get comprehensive analytics summary

### Influencer Marketing (`/api/influencer-marketing/`)
- `GET /brand-opportunities/{user_id}` - Get brand partnership opportunities
- `GET /content-recommendations/{user_id}` - Get content recommendations
- `GET /pricing-recommendations/{user_id}` - Get pricing recommendations
- `GET /growth-strategies/{user_id}` - Get growth strategies
- `GET /marketing-insights/{user_id}` - Get comprehensive marketing insights
- `GET /trending-hashtags` - Get trending hashtags
- `GET /opportunity-alerts/{user_id}` - Get opportunity alerts

### Enhanced AI Agents (`/api/enhanced-ai-agents/`)
- `GET /agent-capabilities` - Get agent capabilities
- `GET /data-sources/status` - Get data sources status
- `GET /enhanced-recommendations/{user_id}` - Get enhanced recommendations
- `POST /execute-with-real-time-data` - Execute agent with real-time data
- `POST /batch-recommendations` - Get batch recommendations from multiple agents
- `GET /recommendation-history/{user_id}` - Get recommendation history

## Configuration

### Environment Variables

```bash
# Enhanced AI Agent Settings
ENHANCED_AI_AGENTS_ENABLED=true
REAL_TIME_DATA_CACHE_TTL=300
MAX_CONCURRENT_AGENT_REQUESTS=10

# Web Search Settings
WEB_SEARCH_ENABLED=true
WEB_SEARCH_API_KEY=your_google_api_key
WEB_SEARCH_ENGINE_ID=your_search_engine_id

# Social Media API Settings
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
YOUTUBE_API_KEY=your_youtube_api_key
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token

# AI Agent Settings
AI_AGENT_TOOL_CALLING_ENABLED=true
AI_AGENT_MCP_ENABLED=true
AI_AGENT_TEMPERATURE=0.7
AI_AGENT_MAX_TOKENS=2000
```

## Usage Examples

### 1. Get Enhanced Recommendations

```python
from app.services.enhanced_ai_agent_service import EnhancedAIAgentService

# Initialize service
ai_service = EnhancedAIAgentService()

# Get growth advisor recommendations with real-time data
recommendations = await ai_service.get_enhanced_recommendations(
    user_id=1,
    agent_type="growth_advisor",
    real_time_context={"platform": "instagram", "niche": "fashion"}
)
```

### 2. Use Web Search Service

```python
from app.services.web_search.web_search_factory import WebSearchFactory

# Create search service (DuckDuckGo by default)
search_service = WebSearchFactory.create_search_service("duckduckgo")

async with search_service:
    # Search for trending content
    results = await search_service.search_trends("influencer marketing", "7d")
    
    # Search for news
    news = await search_service.search_news("social media trends")
```

### 3. Use Social Media APIs

```python
from app.services.social_media.social_media_factory import SocialMediaFactory

# Create Twitter service
twitter_service = SocialMediaFactory.create_social_media_service(
    "twitter", 
    bearer_token="your_bearer_token"
)

async with twitter_service:
    # Get user metrics
    metrics = await twitter_service.get_user_metrics("username")
    
    # Get trending hashtags
    trending = await twitter_service.get_trending_hashtags("twitter", 20)
```

### 4. Use Analytics Service

```python
from app.services.analytics.real_time_analytics import RealTimeAnalyticsService

# Initialize analytics service
analytics = RealTimeAnalyticsService()

# Get engagement trends
trends = await analytics.get_engagement_trends(user_id=1, days=30)

# Get market rates
rates = await analytics.get_market_rates("instagram", "sponsored_post")

# Get competitor analysis
competitors = await analytics.get_competitor_analysis(1, ["competitor1", "competitor2"])
```

## Testing

### API Tests

Run the comprehensive test suite:

```bash
# Test enhanced AI agents
python api-test/api_test_script_runner/test_enhanced_ai_agents.py

# Test real-time services
python api-test/api_test_script_runner/test_real_time_services.py
```

### HTTP Test Files

- `enhanced_ai_agents_tests.http` - Enhanced AI agents API tests
- `real_time_analytics_tests.http` - Real-time analytics API tests
- `influencer_marketing_tests.http` - Influencer marketing API tests

## Database Migrations

The system includes database migrations for:
- Real-time data cache tables
- API usage tracking
- Data source monitoring
- Enhanced AI agent capabilities

Run migrations:

```bash
alembic upgrade head
```

## Performance Considerations

### Caching
- Real-time data is cached for 5 minutes by default
- Cache TTL is configurable via `REAL_TIME_DATA_CACHE_TTL`
- Cache keys include user ID, agent type, and data type

### Rate Limiting
- Each API service has built-in rate limiting
- Rate limits are tracked and enforced
- Fallback mechanisms when rate limits are exceeded

### Error Handling
- Graceful degradation when services are unavailable
- Fallback to legacy implementations
- Comprehensive error logging and monitoring

## Security

### API Keys
- All API keys are stored in environment variables
- No hardcoded credentials in the codebase
- Secure handling of sensitive data

### Data Privacy
- User data is handled according to platform policies
- No unnecessary data storage
- Configurable data retention policies

## Monitoring

### Health Checks
- Real-time data source health monitoring
- API response time tracking
- Error rate monitoring
- Data quality scoring

### Logging
- Comprehensive logging for all operations
- Structured logging for easy analysis
- Performance metrics logging

## Future Enhancements

1. **Machine Learning Integration**: Add ML models for trend prediction
2. **Advanced Analytics**: Implement predictive analytics
3. **Multi-language Support**: Add support for multiple languages
4. **Real-time Notifications**: Push notifications for opportunities
5. **Advanced Caching**: Implement Redis for distributed caching
6. **API Versioning**: Add API versioning for backward compatibility

## Troubleshooting

### Common Issues

1. **API Rate Limits**: Check rate limit status in data sources
2. **Authentication Errors**: Verify API keys and tokens
3. **Data Quality Issues**: Check data source health status
4. **Performance Issues**: Monitor cache hit rates and response times

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Health Check

Check system health:

```bash
curl http://localhost:8000/api/enhanced-ai-agents/data-sources/status
```

## Contributing

1. Follow SOLID principles
2. Use interfaces for new services
3. Add comprehensive tests
4. Update documentation
5. Follow the existing code structure

## License

This enhanced AI agent system is part of the Viral Together platform and follows the same licensing terms.
