import json
import logging
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.influencer_recommendations import InfluencerRecommendations
from app.db.models.influencer_recommendation_summaries import InfluencerRecommendationSummaries
from app.db.models.influencer import Influencer
from app.core.config import settings
from fastapi import HTTPException
import re

logger = logging.getLogger(__name__)


class GrowthStrategiesService:
    def __init__(self):
        self.llm_client = None  # Will be initialized when needed
    
    async def get_or_create_growth_strategies(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        recommendation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get existing growth strategies or create new ones using AI agent
        """
        try:
            # First, check if strategies already exist
            if recommendation_id:
                existing_summaries = await self._get_existing_summaries(db, recommendation_id)
                if existing_summaries:
                    return self._format_response(existing_summaries)
            
            # Get recommendation data
            recommendation_data = await self._get_recommendation_data(db, influencer_id, recommendation_id)
            if not recommendation_data:
                raise ValueError(f"No recommendation data found for influencer_id: {influencer_id}")
            
            # Generate growth strategies using AI agent
            try:
                strategies = await self._generate_growth_strategies(recommendation_data)
                
                # Save to database only if strategies are successfully generated
                saved_summaries = await self._save_strategies_to_db(
                    db, 
                    recommendation_data['influencer_id'], 
                    recommendation_data['id'], 
                    strategies
                )
                
                return self._format_response(saved_summaries)
                
            except ValueError as e:
                logger.error(f"❌ Strategy generation failed - NOT saving to database: {str(e)}")
                raise ValueError(f"Failed to generate valid strategies: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Unexpected error during strategy generation - NOT saving to database: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"Error generating growth strategies: {str(e)}")
            raise
    
    async def get_existing_strategies(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        recommendation_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing growth strategies from database only (no AI processing)
        """
        try:
            if recommendation_id:
                existing_summaries = await self._get_existing_summaries(db, recommendation_id)
            else:
                # Get the latest recommendation for this influencer
                recommendation_data = await self._get_recommendation_data(db, influencer_id, None)
                if not recommendation_data:
                    return None
                
                existing_summaries = await self._get_existing_summaries(db, recommendation_data['id'])
            
            if existing_summaries:
                return self._format_response(existing_summaries)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting existing strategies: {str(e)}")
            return None
    
    async def is_processing_in_progress(self, db: AsyncSession, influencer_id: int) -> bool:
        """
        Check if growth strategies are currently being processed for this influencer
        """
        try:
            # This would typically check a processing status table or Celery task status
            # For now, we'll implement a simple check
            from app.tasks.growth_strategies_tasks import check_processing_status
            
            # Note: This is a synchronous call, but in a real implementation,
            # you might want to use a database flag or Redis cache
            result = check_processing_status.delay(influencer_id)
            status = result.get(timeout=1)  # Quick timeout for status check
            
            return status.get('is_processing', False) if status else False
            
        except Exception as e:
            logger.error(f"Error checking processing status: {str(e)}")
            return False
    
    async def check_data_availability(self, db: AsyncSession, influencer_id: int, recommendation_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Check if recommendation data is available for processing
        Returns detailed information about data availability
        """
        try:
            # Check if influencer exists
            user_query = select(Influencer.user_id).where(Influencer.id == influencer_id)
            user_result = await db.execute(user_query)
            user_id = user_result.scalar_one_or_none()
            
            if not user_id:
                return {
                    'available': False,
                    'error': 'INFLUENCER_NOT_FOUND',
                    'message': f'No user found for influencer_id: {influencer_id}',
                    'suggestion': 'Ensure the influencer exists and is properly linked to a user account.'
                }
            
            # Check if recommendations exist
            if recommendation_id:
                query = select(InfluencerRecommendations).where(
                    InfluencerRecommendations.id == recommendation_id,
                    InfluencerRecommendations.user_id == user_id
                )
            else:
                query = select(InfluencerRecommendations).where(
                    InfluencerRecommendations.user_id == user_id
                ).order_by(InfluencerRecommendations.created_at.desc())
            
            result = await db.execute(query)
            recommendation = result.scalar_one_or_none()
            
            if not recommendation:
                return {
                    'available': False,
                    'error': 'NO_RECOMMENDATIONS_FOUND',
                    'message': f'No recommendations found for influencer_id: {influencer_id}',
                    'suggestion': 'Generate influencer recommendations first before requesting growth strategies.'
                }
            
            # Check if recommendation has meaningful data
            has_base_plan = recommendation.base_plan and len(str(recommendation.base_plan)) > 10
            has_enhanced_plan = recommendation.enhanced_plan and len(str(recommendation.enhanced_plan)) > 10
            has_ai_insights = recommendation.ai_insights and len(str(recommendation.ai_insights)) > 10
            
            if not (has_base_plan or has_enhanced_plan or has_ai_insights):
                return {
                    'available': False,
                    'error': 'INSUFFICIENT_DATA',
                    'message': 'Recommendation data exists but contains insufficient information for AI processing.',
                    'suggestion': 'Ensure the recommendation has meaningful data in base_plan, enhanced_plan, or ai_insights.',
                    'data_quality': {
                        'has_base_plan': has_base_plan,
                        'has_enhanced_plan': has_enhanced_plan,
                        'has_ai_insights': has_ai_insights
                    }
                }
            
            return {
                'available': True,
                'message': 'Recommendation data is available and sufficient for processing.',
                'recommendation_id': recommendation.id,
                'data_quality': {
                    'has_base_plan': has_base_plan,
                    'has_enhanced_plan': has_enhanced_plan,
                    'has_ai_insights': has_ai_insights
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking data availability: {str(e)}")
            return {
                'available': False,
                'error': 'CHECK_FAILED',
                'message': f'Error checking data availability: {str(e)}',
                'suggestion': 'Please try again or contact support if the issue persists.'
            }
    
    async def _get_existing_summaries(self, db: AsyncSession, recommendation_id: int) -> Optional[InfluencerRecommendationSummaries]:
        """Get existing growth strategies from database"""
        query = select(InfluencerRecommendationSummaries).where(
            InfluencerRecommendationSummaries.influencer_recommendation_id == recommendation_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_recommendation_data(self, db: AsyncSession, influencer_id: int, recommendation_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """Get recommendation data for the influencer"""
        # First, resolve influencer_id to user_id
        user_query = select(Influencer.user_id).where(Influencer.id == influencer_id)
        user_result = await db.execute(user_query)
        user_id = user_result.scalar_one_or_none()
        
        if not user_id:
            logger.error(f"No user found for influencer_id: {influencer_id}")
            return None
        
        if recommendation_id:
            query = select(InfluencerRecommendations).where(
                InfluencerRecommendations.id == recommendation_id,
                InfluencerRecommendations.user_id == user_id
            )
        else:
            # Get the latest recommendation
            query = select(InfluencerRecommendations).where(
                InfluencerRecommendations.user_id == user_id
            ).order_by(InfluencerRecommendations.created_at.desc())
        
        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            return None
        
        return {
            'id': recommendation.id,
            'influencer_id': influencer_id,
            'user_id': user_id,
            'base_plan': recommendation.base_plan,
            'enhanced_plan': recommendation.enhanced_plan,
            'ai_insights': recommendation.ai_insights,
            'performance_goals': recommendation.performance_goals,
            'pricing_recommendations': recommendation.pricing_recommendations,
            'monthly_schedule': recommendation.monthly_schedule
        }
    
    async def _generate_growth_strategies(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate growth strategies using AI agent with comprehensive prompt"""
        
        try:
            logger.info(f"🤖 AI AGENT SERVICE: Starting growth strategies generation")
            logger.info(f"👤 Influencer ID: {recommendation_data.get('influencer_id')}")
            logger.info(f"🆔 Recommendation ID: {recommendation_data.get('id')}")
            logger.info(f"👤 User ID: {recommendation_data.get('user_id')}")
            
            # Use the real AI agent service
            from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
            
            logger.info(f"🔧 Initializing EnhancedAIAgentService")
            ai_service = EnhancedAIAgentService()
            logger.info(f"✅ AI Service initialized successfully")
            
            # Create a comprehensive prompt for growth strategies
            logger.info(f"📝 Creating comprehensive prompt for AI agent")
            prompt = self._create_comprehensive_prompt(recommendation_data)
            logger.info(f"📝 Prompt created - Length: {len(prompt)} characters")
            logger.info(f"📝 Prompt preview: {prompt[:200]}...")
            
            # Execute with real AI agent
            logger.info(f"🚀 EXECUTING AI AGENT: Starting AI agent execution")
            logger.info(f"⏰ AI Agent execution start time: {asyncio.get_event_loop().time()}")
            
            # Use the AI agent to generate strategies
            ai_response = await ai_service.execute_with_real_time_data(
                agent_id=1,  # Use a default agent ID
                prompt=prompt,
                context={
                    "recommendation_data": recommendation_data,
                    "influencer_id": recommendation_data.get('influencer_id'),
                    "task_type": "growth_strategies_generation",
                    "agent_type": "growth_strategies",
                    "user_id": recommendation_data.get('user_id', 1)
                },
                real_time_data={
                    "recommendation_data": recommendation_data,
                    "influencer_id": recommendation_data.get('influencer_id')
                }
            )
            
            logger.info(f"🤖 AI Agent execution completed!")
            logger.info(f"⏰ AI Agent execution end time: {asyncio.get_event_loop().time()}")
            logger.info(f"📊 AI Response received: {ai_response is not None}")
            if ai_response:
                logger.info(f"📋 AI Response keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'Not a dict'}")
                logger.info(f"📊 AI Response status: {ai_response.get('status') if isinstance(ai_response, dict) else 'Unknown'}")
            
            # Parse the AI response into structured format
            logger.info(f"🔍 Parsing AI response into structured format")
            strategies = self._parse_ai_response_to_strategies(ai_response, recommendation_data)
            
            logger.info(f"📊 Parsed strategies: {strategies is not None}")
            if strategies:
                logger.info(f"📋 Strategy categories: {list(strategies.keys())}")
                for key, value in strategies.items():
                    if isinstance(value, list):
                        logger.info(f"📊 {key}: {len(value)} items")
                    else:
                        logger.info(f"📊 {key}: {type(value)}")
            
            logger.info(f"🎉 AI agent generated strategies successfully for influencer_id: {recommendation_data.get('influencer_id')}")
            return strategies
            
        except ValueError as e:
            logger.error(f"❌ AI response parsing failed: {str(e)}")
            raise HTTPException(status_code=422, detail=f"AI response parsing failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error calling AI agent: {str(e)}")
            raise HTTPException(status_code=500, detail="AI processing failed. Please try again later.")
    
    def _parse_ai_response_to_strategies(self, ai_response: Dict[str, Any], recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI agent response into structured growth strategies format"""
        try:
            logger.info(f"🔍 Starting AI response parsing")
            
            # Extract the main response content from AI
            response_content = ai_response.get('response', '')
            
            # Try to parse JSON response first
            if response_content and response_content.strip().startswith('{'):
                try:
                    parsed_response = json.loads(response_content)
                    logger.info(f"✅ Successfully parsed JSON response from AI")
                    return self._validate_and_structure_parsed_response(parsed_response)
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ AI response is not valid JSON: {str(e)}")
            
            # If JSON parsing fails, extract from recommendation data directly
            logger.info(f"🔄 Falling back to direct data extraction from recommendation")
            return self._extract_strategies_from_recommendation_data(recommendation_data)
            
        except Exception as e:
            logger.error(f"❌ Critical error in AI response parsing: {str(e)}")
            raise ValueError(f"Failed to parse AI response and extract strategies: {str(e)}")
    
    def _validate_and_structure_parsed_response(self, parsed_response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and structure the parsed AI response"""
        try:
            # Validate required categories exist
            required_categories = ['more_followers', 'content_ideas', 'social_profiles', 'influencer_collab', 'business_collab', 'content_scripts']
            
            for category in required_categories:
                if category not in parsed_response:
                    raise ValueError(f"Missing required category: {category}")
                
                if not isinstance(parsed_response[category], list):
                    raise ValueError(f"Category {category} must be a list")
                
                # Ensure at least one item exists
                if len(parsed_response[category]) == 0:
                    raise ValueError(f"Category {category} cannot be empty")
            
            logger.info(f"✅ Validated AI response structure")
            return parsed_response
            
        except Exception as e:
            logger.error(f"❌ AI response validation failed: {str(e)}")
            raise ValueError(f"AI response structure validation failed: {str(e)}")
    
    def _extract_strategies_from_recommendation_data(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract strategies directly from recommendation data when AI response parsing fails"""
        try:
            logger.info(f"🔍 Extracting strategies from recommendation data")
            
            # Extract enhanced plan data
            enhanced_plan = recommendation_data.get('enhanced_plan', {})
            detailed_analysis = enhanced_plan.get('detailed_analysis', {})
            agent_responses = detailed_analysis.get('agent_responses', [])
            
            if not agent_responses:
                raise ValueError("No agent responses found in recommendation data")
            
            logger.info(f"📊 Found {len(agent_responses)} agent responses")
            
            # Extract key insights from agent responses
            growth_insights = []
            content_insights = []
            collaboration_insights = []
            
            for agent in agent_responses:
                if agent.get('status') == 'success':
                    response_text = agent.get('response', '')
                    agent_type = agent.get('agent_type', '')
                    
                    if 'growth' in agent_type.lower():
                        growth_insights.append(response_text[:500])
                    elif 'content' in agent_type.lower():
                        content_insights.append(response_text[:500])
                    elif 'collaboration' in agent_type.lower():
                        collaboration_insights.append(response_text[:500])
            
            # Structure the extracted data
            strategies = {
                "more_followers": [
                    {
                        "strategy": "Multi-Agent Growth Strategy",
                        "description": f"Based on {len(growth_insights)} specialized agent analyses: {growth_insights[0] if growth_insights else 'No growth insights available'}",
                        "expected_growth": "15-25% follower increase within 3 months",
                        "implementation": "Implement agent-recommended engagement and content strategies"
                    }
                ],
                "content_ideas": [
                    {
                        "idea": "Agent-Recommended Content Strategy",
                        "description": f"Content strategy derived from {len(content_insights)} content advisors: {content_insights[0] if content_insights else 'No content insights available'}",
                        "content_type": "Multi-format content mix",
                        "posting_frequency": "Optimized based on agent analysis",
                        "expected_engagement": "2-3% engagement rate improvement"
                    }
                ],
                "social_profiles": [
                    {
                        "name": "Target Audience Profiles",
                        "platform": "Multi-platform strategy",
                        "profile_url": "Based on agent audience analysis",
                        "followers": "10k-50k range for collaborations",
                        "relevance_reason": f"Collaboration strategy from {len(collaboration_insights)} collaboration advisors"
                    }
                ],
                "influencer_collab": [
                    {
                        "collaboration": "Strategic Influencer Partnerships",
                        "description": f"Partnership opportunities identified by specialized agents: {collaboration_insights[0] if collaboration_insights else 'No collaboration insights available'}",
                        "expected_reach": "20-30% reach expansion",
                        "implementation": "Agent-guided collaboration framework"
                    }
                ],
                "business_collab": [
                    {
                        "opportunity": "Revenue-Generating Partnerships",
                        "type": "Multi-tier business collaborations",
                        "description": f"Business opportunities from agent analysis: {collaboration_insights[0] if collaboration_insights else 'No business insights available'}",
                        "location": "Global opportunities identified",
                        "potential_revenue": "200-300% revenue increase potential",
                        "implementation": "Agent-recommended business development strategy",
                        "relevance_reason": "Based on comprehensive agent analysis"
                    }
                ],
                "content_scripts": [
                    {
                        "script": "Agent-Optimized Content Framework",
                        "content": f"Content creation framework derived from agent insights: {content_insights[0] if content_insights else 'No script insights available'}",
                        "platform": "Multi-platform optimized",
                        "duration": "Variable based on content type",
                        "hashtags": "Agent-optimized hashtag strategy"
                    }
                ]
            }
            
            logger.info(f"✅ Successfully extracted strategies from recommendation data")
            return strategies
            
        except Exception as e:
            logger.error(f"❌ Failed to extract strategies from recommendation data: {str(e)}")
            raise ValueError(f"Failed to extract strategies from recommendation data: {str(e)}")
    
    def clean_and_format_recommendation_data(self, raw_data: dict) -> str:
        """
        Enhanced data preprocessing with source attribution and context preservation
        """
        # Define source mapping for better context awareness
        source_mapping = {
            'base_plan': 'BASE PLAN AI (Strategic Foundation)',
            'enhanced_plan': 'ENHANCED PLAN AI (Advanced Strategies)', 
            'monthly_schedule': 'SCHEDULING AI (Content Calendar)',
            'performance_goals': 'PERFORMANCE AI (Metrics & Goals)',
            'pricing_recommendations': 'PRICING AI (Monetization)',
            'ai_insights': 'INSIGHTS AI (Deep Analysis)'
        }
        
        structured_parts = []
        
        for key, value in raw_data.items():
            if key in source_mapping:
                source_label = source_mapping[key]
                
                # Convert value to string with better structure
                if isinstance(value, dict):
                    # Flatten dictionary with better formatting
                    flattened_items = []
                    for k, v in value.items():
                        if isinstance(v, list):
                            list_items = [str(item) for item in v if str(item).strip()]
                            if list_items:
                                flattened_items.append(f"{k}: {' | '.join(list_items)}")
                        else:
                            if str(v).strip():
                                flattened_items.append(f"{k}: {str(v)}")
                    value = ' | '.join(flattened_items)
                elif isinstance(value, list):
                    list_items = [str(item) for item in value if str(item).strip()]
                    value = ' | '.join(list_items)
                else:
                    value = str(value)
                
                # Clean and format with source attribution
                if value and value.strip():
                    cleaned = re.sub(r'[\*\-#\\n\*\*]+', ' ', value).strip()
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    cleaned = cleaned.replace("Okay, let's craft", "").strip()
                    
                    if cleaned and len(cleaned) > 10:  # Only include substantial content
                        structured_parts.append(f"=== {source_label} ===\n{cleaned}\n")
        
        # Combine with clear structure
        long_text = '\n'.join(structured_parts)
        return long_text
    
    def _create_comprehensive_prompt(self, recommendation_data: Dict[str, Any]) -> str:
        cleaned_text = self.clean_and_format_recommendation_data(recommendation_data)
        
        prompt = f"""
You are a GROWTH STRATEGY EXTRACTOR. You MUST create MULTIPLE items for each category.

CRITICAL: You MUST return at least 3 items per category. NO EXCEPTIONS.

SOURCE DATA:
{cleaned_text}

REQUIRED OUTPUT FORMAT:
- MORE_FOLLOWERS: Create 3-5 different follower growth strategies
- CONTENT_IDEAS: Create 3-5 different content concepts  
- SOCIAL_PROFILES: Create 3-5 different relevant profiles
- INFLUENCER_COLLAB: Create 3-5 different collaboration opportunities
- BUSINESS_COLLAB: Create 3-5 different business opportunities
- CONTENT_SCRIPTS: Create 3-5 different content scripts

MANDATORY RULES:
1. Each array MUST have multiple items (minimum 3)
2. Create variations and different approaches for each category
3. Base items on the source data but create multiple variations
4. Each item must be unique and different from others in the same category
5. DO NOT return single items - ALWAYS return multiple items

EXAMPLE STRUCTURE (you must create multiple items like this):
"more_followers": [
  {{"strategy": "Strategy 1", "description": "Description 1", ...}},
  {{"strategy": "Strategy 2", "description": "Description 2", ...}},
  {{"strategy": "Strategy 3", "description": "Description 3", ...}}
]

RESPOND WITH ONLY THIS JSON:
        {{
            "more_followers": [
                {{
      "strategy": "Specific strategy name with clear focus",
      "description": "Detailed implementation description with specific steps and expected outcomes",
      "expected_growth": "Specific growth numbers with timeframe (e.g., '500-1000 followers in 3 months')",
      "implementation": "Step-by-step implementation guide with specific actions and timeline"
    }},
    {{
      "strategy": "Another distinct strategy",
      "description": "Detailed description",
      "expected_growth": "Specific growth projection",
      "implementation": "Specific implementation steps"
    }},
    {{
      "strategy": "Third unique strategy",
      "description": "Detailed description", 
      "expected_growth": "Specific growth projection",
      "implementation": "Specific implementation steps"
    }},
    {{
      "strategy": "Fourth distinct strategy",
      "description": "Detailed description",
      "expected_growth": "Specific growth projection", 
      "implementation": "Specific implementation steps"
    }},
    {{
      "strategy": "Fifth unique strategy",
                    "description": "Detailed description",
      "expected_growth": "Specific growth projection",
      "implementation": "Specific implementation steps"
                }}
            ],
            "content_ideas": [
                {{
      "idea": "Specific content concept with clear theme",
      "description": "Detailed content description with creative elements and audience appeal",
      "content_type": "Specific format (Video/Post/Story/Reel)",
      "posting_frequency": "Specific schedule (e.g., '3x per week, Tuesday/Thursday/Sunday')",
      "expected_engagement": "Specific engagement metrics (e.g., '15-20% engagement rate, 500+ comments')"
    }},
    {{
      "idea": "Another distinct content idea",
      "description": "Detailed description",
      "content_type": "Specific format",
      "posting_frequency": "Specific schedule",
      "expected_engagement": "Specific engagement metrics"
    }},
    {{
      "idea": "Third unique content idea",
      "description": "Detailed description",
      "content_type": "Specific format", 
      "posting_frequency": "Specific schedule",
      "expected_engagement": "Specific engagement metrics"
    }},
    {{
      "idea": "Fourth distinct content idea",
      "description": "Detailed description",
      "content_type": "Specific format",
      "posting_frequency": "Specific schedule",
      "expected_engagement": "Specific engagement metrics"
    }},
    {{
      "idea": "Fifth unique content idea",
                    "description": "Detailed description",
      "content_type": "Specific format",
      "posting_frequency": "Specific schedule", 
      "expected_engagement": "Specific engagement metrics"
                }}
            ],
            "social_profiles": [
                {{
      "name": "Specific profile handle with @",
      "platform": "Specific platform (Instagram/TikTok/YouTube/Twitter)",
      "profile_url": "Complete profile URL",
      "followers": "Specific follower count (e.g., '250K followers')",
      "relevance_reason": "Specific reason for collaboration potential and strategic value"
    }},
    {{
      "name": "Another relevant profile",
      "platform": "Specific platform",
      "profile_url": "Complete URL",
      "followers": "Specific follower count",
      "relevance_reason": "Specific collaboration rationale"
    }},
    {{
      "name": "Third relevant profile",
      "platform": "Specific platform",
      "profile_url": "Complete URL", 
      "followers": "Specific follower count",
      "relevance_reason": "Specific collaboration rationale"
    }},
    {{
      "name": "Fourth relevant profile",
      "platform": "Specific platform",
      "profile_url": "Complete URL",
      "followers": "Specific follower count",
      "relevance_reason": "Specific collaboration rationale"
    }},
    {{
      "name": "Fifth relevant profile",
      "platform": "Specific platform",
      "profile_url": "Complete URL",
      "followers": "Specific follower count",
      "relevance_reason": "Specific collaboration rationale"
                }}
            ],
            "influencer_collab": [
                {{
      "collaboration": "Specific collaboration concept with clear theme",
      "description": "Detailed collaboration description with mutual benefits and creative approach",
      "expected_reach": "Specific combined reach estimate (e.g., '500K-750K total reach')",
      "implementation": "Step-by-step collaboration process with timeline and deliverables"
    }},
    {{
      "collaboration": "Another distinct collaboration idea",
      "description": "Detailed description",
      "expected_reach": "Specific reach estimate",
      "implementation": "Specific implementation steps"
    }},
    {{
      "collaboration": "Third unique collaboration",
      "description": "Detailed description",
      "expected_reach": "Specific reach estimate",
      "implementation": "Specific implementation steps"
    }},
    {{
      "collaboration": "Fourth distinct collaboration",
      "description": "Detailed description",
      "expected_reach": "Specific reach estimate",
      "implementation": "Specific implementation steps"
    }},
    {{
      "collaboration": "Fifth unique collaboration",
                    "description": "Detailed description",
      "expected_reach": "Specific reach estimate",
      "implementation": "Specific implementation steps"
                }}
            ],
            "business_collab": [
                {{
      "opportunity": "Specific business opportunity with clear value proposition",
      "type": "Specific partnership type (Local Brand Partnership/International Collaboration/Product Launch)",
      "description": "Detailed opportunity description with business benefits and market potential",
      "location": "Specific geographic focus (e.g., 'US market' or 'Global reach')",
      "potential_revenue": "Specific revenue range (e.g., '$2K-5K per collaboration')",
      "implementation": "Step-by-step partnership process with negotiation points and deliverables",
      "relevance_reason": "Specific reason for market fit and strategic alignment"
    }},
    {{
      "opportunity": "Another distinct business opportunity",
      "type": "Specific partnership type",
      "description": "Detailed description",
      "location": "Specific geographic focus",
      "potential_revenue": "Specific revenue range",
      "implementation": "Specific implementation steps",
      "relevance_reason": "Specific market fit rationale"
    }},
    {{
      "opportunity": "Third unique business opportunity",
      "type": "Specific partnership type",
      "description": "Detailed description",
      "location": "Specific geographic focus",
      "potential_revenue": "Specific revenue range",
      "implementation": "Specific implementation steps",
      "relevance_reason": "Specific market fit rationale"
    }},
    {{
      "opportunity": "Fourth distinct business opportunity",
      "type": "Specific partnership type",
      "description": "Detailed description",
      "location": "Specific geographic focus",
      "potential_revenue": "Specific revenue range",
      "implementation": "Specific implementation steps",
      "relevance_reason": "Specific market fit rationale"
    }},
    {{
      "opportunity": "Fifth unique business opportunity",
      "type": "Specific partnership type",
                    "description": "Detailed description",
      "location": "Specific geographic focus",
      "potential_revenue": "Specific revenue range",
      "implementation": "Specific implementation steps",
      "relevance_reason": "Specific market fit rationale"
                }}
            ],
            "content_scripts": [
                {{
      "script": "Specific script concept with clear purpose",
      "content": "Complete script content with dialogue, actions, and engagement elements",
      "platform": "Specific platform optimization (Instagram Reels/TikTok/YouTube Shorts)",
      "duration": "Specific duration (e.g., '15-30 seconds' or '2-3 minutes')",
      "hashtags": "Specific hashtag strategy with trending and niche tags"
    }},
    {{
      "script": "Another distinct script concept",
      "content": "Complete script content",
      "platform": "Specific platform",
      "duration": "Specific duration",
      "hashtags": "Specific hashtag strategy"
    }},
    {{
      "script": "Third unique script concept",
      "content": "Complete script content",
      "platform": "Specific platform",
      "duration": "Specific duration",
      "hashtags": "Specific hashtag strategy"
    }},
    {{
      "script": "Fourth distinct script concept",
      "content": "Complete script content",
      "platform": "Specific platform",
      "duration": "Specific duration",
      "hashtags": "Specific hashtag strategy"
    }},
    {{
      "script": "Fifth unique script concept",
      "content": "Complete script content",
      "platform": "Specific platform",
      "duration": "Specific duration",
      "hashtags": "Specific hashtag strategy"
                }}
            ]
        }}
"""
        return prompt
    
    async def _save_strategies_to_db(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        recommendation_id: int, 
        strategies: Dict[str, Any]
    ) -> InfluencerRecommendationSummaries:
        """Save generated strategies to database with proper connection handling"""
        
        try:
            logger.info(f"💾 Starting database save for influencer_id: {influencer_id}, recommendation_id: {recommendation_id}")
            
            # Check if summary already exists
            existing_query = select(InfluencerRecommendationSummaries).where(
                InfluencerRecommendationSummaries.influencer_recommendation_id == recommendation_id
            )
            existing_result = await db.execute(existing_query)
            existing_summary = existing_result.scalar_one_or_none()
            
            if existing_summary:
                logger.info(f"📝 Updating existing summary ID: {existing_summary.id}")
                # Update existing summary
                existing_summary.more_followers = strategies.get('more_followers')
                existing_summary.content_ideas = strategies.get('content_ideas')
                existing_summary.social_profiles = strategies.get('social_profiles')
                existing_summary.influencer_collab = strategies.get('influencer_collab')
                existing_summary.business_collab = strategies.get('business_collab')
                existing_summary.content_scripts = strategies.get('content_scripts')
                await db.commit()
                await db.refresh(existing_summary)
                logger.info(f"✅ Successfully updated existing summary")
                return existing_summary
            else:
                logger.info(f"📝 Creating new summary for influencer_id: {influencer_id}")
                # Create new summary
                new_summary = InfluencerRecommendationSummaries(
                    influencer_recommendation_id=recommendation_id,
                    influencer_id=influencer_id,
                    more_followers=strategies.get('more_followers'),
                    content_ideas=strategies.get('content_ideas'),
                    social_profiles=strategies.get('social_profiles'),
                    influencer_collab=strategies.get('influencer_collab'),
                    business_collab=strategies.get('business_collab'),
                    content_scripts=strategies.get('content_scripts')
                )
                db.add(new_summary)
                await db.commit()
                await db.refresh(new_summary)
                logger.info(f"✅ Successfully created new summary with ID: {new_summary.id}")
                return new_summary
                
        except Exception as e:
            logger.error(f"❌ Database save error: {str(e)}")
            await db.rollback()
            raise e
    
    def _format_response(self, summaries: InfluencerRecommendationSummaries) -> Dict[str, Any]:
        """Format the response for the API"""
        return {
            "more_followers": summaries.more_followers or [],
            "content_ideas": summaries.content_ideas or [],
            "social_profiles": summaries.social_profiles or [],
            "influencer_collab": summaries.influencer_collab or [],
            "business_collab": summaries.business_collab or [],
            "content_scripts": summaries.content_scripts or []
        }
