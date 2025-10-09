import json
import logging
import re
import asyncio
import httpx # Added for link verification
import random
import time # Added for rate limiting
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.influencer_recommendations import InfluencerRecommendations
from app.db.models.influencer_recommendation_summaries import InfluencerRecommendationSummaries
from app.db.models.influencer import Influencer
from app.db.models.location import InfluencerOperationalLocation # Import location model
from app.services.web_search.duckduckgo_search import DuckDuckGoSearchService # Import the real DuckDuckGo search service

logger = logging.getLogger(__name__)


class NonAIStrategyService:
    """
    Non-AI strategy generation service using rule-based approach
    """
    
    def __init__(self):
        self.strategy_templates = self._load_strategy_templates()
        self.search_cache = {}  # Cache for search results to avoid repeated API calls
    
    def clear_search_cache(self):
        """Clear the search cache to free memory"""
        self.search_cache.clear()
        logger.info("🗑️ Search cache cleared")
    
    async def generate_download_files(self, summary_data: Dict[str, Any], summary_id: int) -> List[Dict[str, str]]:
        """Generate PDF files and return download links"""
        download_links = []
        
        # Ensure downloads directory exists
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Generate files for each category that has data
        categories = {
            "more_followers": "More Followers Implementation Guide",
            "content_ideas": "Content Ideas Playbook", 
            "social_profiles": "Social Media Profiles Optimization",
            "influencer_collab": "Influencer Collaboration Handbook",
            "business_collab": "Business Collaboration Strategies",
            "content_scripts": "Content Scripts Library"
        }
        
        for category, title in categories.items():
            if category in summary_data and summary_data[category]:
                try:
                    # Generate unique filename
                    filename = f"{category}_{summary_id}_{uuid.uuid4().hex[:8]}.pdf"
                    filepath = os.path.join(downloads_dir, filename)
                    
                    # Generate PDF content
                    await self._generate_pdf_file(filepath, title, summary_data[category])
                    
                    # Create download link
                    download_link = {
                        "title": title,
                        "category": category,
                        "filename": filename,
                        "download_url": f"http://localhost:8000/api/downloads/files/{filename}",
                        "size": f"{os.path.getsize(filepath) // 1024} KB"
                    }
                    download_links.append(download_link)
                    
                    logger.info(f"✅ Generated {title}: {filename}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate {title}: {str(e)}")
        
        return download_links
    
    async def _generate_pdf_file(self, filepath: str, title: str, content: Any):
        """Generate a PDF file from content"""
        try:
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            title_style = styles['Title']
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Add content based on type
            if isinstance(content, list):
                for i, item in enumerate(content, 1):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {str(value)}", styles['Normal']))
                            story.append(Spacer(1, 6))
                    else:
                        story.append(Paragraph(f"{i}. {str(item)}", styles['Normal']))
                        story.append(Spacer(1, 6))
            elif isinstance(content, dict):
                for key, value in content.items():
                    story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Heading2']))
                    if isinstance(value, list):
                        for i, item in enumerate(value, 1):
                            story.append(Paragraph(f"{i}. {str(item)}", styles['Normal']))
                            story.append(Spacer(1, 6))
                    else:
                        story.append(Paragraph(str(value), styles['Normal']))
                        story.append(Spacer(1, 6))
            else:
                story.append(Paragraph(str(content), styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            logger.error(f"Error generating PDF {filepath}: {str(e)}")
            raise
    
    
    def _load_strategy_templates(self) -> Dict[str, List[Dict]]:
        """Load predefined strategy templates"""
        return {
            "more_followers": [
                {
                    "strategy": "Consistent Posting Schedule",
                    "description": "Maintain a regular posting schedule to build audience expectation and engagement",
                    "expected_growth": "200-500 followers per month",
                    "implementation": "Post 3-5 times per week at consistent times, use content calendar planning"
                },
                {
                    "strategy": "Engagement-First Approach",
                    "description": "Focus on responding to comments and messages to build community loyalty",
                    "expected_growth": "150-300 followers per month",
                    "implementation": "Respond to all comments within 2 hours, ask questions in captions"
                },
                {
                    "strategy": "Hashtag Optimization",
                    "description": "Use relevant and trending hashtags to increase discoverability",
                    "expected_growth": "100-250 followers per month",
                    "implementation": "Research trending hashtags in your niche, use 15-20 hashtags per post"
                },
                {
                    "strategy": "Cross-Platform Promotion",
                    "description": "Promote content across multiple social media platforms",
                    "expected_growth": "300-600 followers per month",
                    "implementation": "Share Instagram posts on Twitter, create YouTube Shorts from Instagram content"
                },
                {
                    "strategy": "Collaboration Network",
                    "description": "Partner with other influencers to expand reach and gain followers",
                    "expected_growth": "500-1000 followers per collaboration",
                    "implementation": "Reach out to 5-10 influencers monthly for collaboration opportunities"
                }
            ],
            "content_ideas": [
                {
                    "idea": "Behind-the-Scenes Content",
                    "description": "Show your daily routine, workspace, or creative process to build personal connection",
                    "content_type": "Video/Story",
                    "posting_frequency": "2-3 times per week",
                    "expected_engagement": "20-25% engagement rate"
                },
                {
                    "idea": "Educational Tutorials",
                    "description": "Share knowledge and skills related to your niche to provide value",
                    "content_type": "Video/Post",
                    "posting_frequency": "1-2 times per week",
                    "expected_engagement": "15-20% engagement rate"
                },
                {
                    "idea": "Trending Topic Commentary",
                    "description": "Share your perspective on current events or trending topics in your niche",
                    "content_type": "Post/Story",
                    "posting_frequency": "2-4 times per week",
                    "expected_engagement": "18-22% engagement rate"
                },
                {
                    "idea": "User-Generated Content",
                    "description": "Feature content from your followers to build community",
                    "content_type": "Post/Story",
                    "posting_frequency": "1-2 times per week",
                    "expected_engagement": "25-30% engagement rate"
                },
                {
                    "idea": "Interactive Content",
                    "description": "Create polls, Q&As, and challenges to encourage participation",
                    "content_type": "Story/Post",
                    "posting_frequency": "3-5 times per week",
                    "expected_engagement": "30-35% engagement rate"
                }
            ],
            "social_profiles": [
                {
                    "name": "@microinfluencer_network",
                    "platform": "Instagram",
                    "profile_url": "https://instagram.com/microinfluencer_network",
                    "followers": "25K followers",
                    "relevance_reason": "Networking group for micro-influencers in your niche"
                },
                {
                    "name": "@collaboration_hub",
                    "platform": "Instagram",
                    "profile_url": "https://instagram.com/collaboration_hub",
                    "followers": "50K followers",
                    "relevance_reason": "Platform connecting influencers for collaboration opportunities"
                },
                {
                    "name": "@brand_partnerships",
                    "platform": "Instagram",
                    "profile_url": "https://instagram.com/brand_partnerships",
                    "followers": "100K followers",
                    "relevance_reason": "Brand partnership opportunities and networking"
                },
                {
                    "name": "@content_creators",
                    "platform": "TikTok",
                    "profile_url": "https://tiktok.com/@content_creators",
                    "followers": "200K followers",
                    "relevance_reason": "Content creator community for cross-promotion"
                },
                {
                    "name": "@influencer_growth",
                    "platform": "YouTube",
                    "profile_url": "https://youtube.com/@influencer_growth",
                    "followers": "75K followers",
                    "relevance_reason": "Educational content about influencer growth strategies"
                }
            ],
            "influencer_collab": [
                {
                    "collaboration": "Cross-Promotion Partnership",
                    "description": "Partner with influencers in similar niches to cross-promote content",
                    "expected_reach": "Combined reach of 50K-100K",
                    "implementation": "Identify 3-5 influencers, propose content exchange, create shared content"
                },
                {
                    "collaboration": "Joint Live Stream",
                    "description": "Host live sessions together to engage both audiences",
                    "expected_reach": "Live audience of 500-2000 viewers",
                    "implementation": "Schedule monthly live sessions, promote across platforms"
                },
                {
                    "collaboration": "Content Series Collaboration",
                    "description": "Create a multi-part content series with another influencer",
                    "expected_reach": "Series reach of 25K-75K per episode",
                    "implementation": "Plan 4-6 episode series, alternate posting schedules"
                },
                {
                    "collaboration": "Challenge Campaign",
                    "description": "Create a social media challenge with other influencers",
                    "expected_reach": "Challenge participation of 1000-5000 users",
                    "implementation": "Design challenge concept, recruit 5-10 influencers, launch campaign"
                },
                {
                    "collaboration": "Podcast Guest Exchange",
                    "description": "Appear on each other's podcasts or create joint episodes",
                    "expected_reach": "Podcast audience of 10K-50K",
                    "implementation": "Schedule recording sessions, cross-promote episodes"
                }
            ],
            "business_collab": [
                {
                    "opportunity": "Local Brand Partnership",
                    "type": "Local Brand Partnership",
                    "description": "Partner with local businesses for sponsored content and events",
                    "location": "Local market focus",
                    "potential_revenue": "$500-2000 per collaboration",
                    "implementation": "Research local brands, create partnership proposals, negotiate rates",
                    "relevance_reason": "Local market alignment and community connection"
                },
                {
                    "opportunity": "Product Launch Collaboration",
                    "type": "Product Launch",
                    "description": "Partner with brands for new product launches and reviews",
                    "location": "National/International reach",
                    "potential_revenue": "$1000-5000 per launch",
                    "implementation": "Build brand relationships, create launch content, track performance",
                    "relevance_reason": "High-value partnerships with measurable ROI"
                },
                {
                    "opportunity": "Affiliate Marketing Program",
                    "type": "Affiliate Marketing",
                    "description": "Earn commissions by promoting products and services",
                    "location": "Global reach",
                    "potential_revenue": "$200-1000 per month",
                    "implementation": "Join affiliate networks, create promotional content, track conversions",
                    "relevance_reason": "Passive income stream with scalable potential"
                },
                {
                    "opportunity": "Event Partnership",
                    "type": "Event Partnership",
                    "description": "Partner with brands for events, workshops, and meetups",
                    "location": "Local/Regional events",
                    "potential_revenue": "$1000-3000 per event",
                    "implementation": "Plan event concepts, secure brand sponsors, execute events",
                    "relevance_reason": "High-engagement opportunities with direct audience interaction"
                },
                {
                    "opportunity": "Long-term Brand Ambassadorship",
                    "type": "Brand Ambassadorship",
                    "description": "Become a long-term brand ambassador for consistent partnerships",
                    "location": "National/International",
                    "potential_revenue": "$2000-10000 per month",
                    "implementation": "Build strong brand relationships, create ongoing content, maintain partnership",
                    "relevance_reason": "Stable income with long-term growth potential"
                }
            ],
            "content_scripts": [
                {
                    "script": "Day-in-the-Life Vlog",
                    "content": "Good morning! Today I'm going to show you my typical day as a [niche] creator. First, I start with my morning routine... [Show morning routine] Then I head to my workspace where I plan my content... [Show planning process] Later, I'll be creating today's main content... [Show creation process] What's your favorite part of your day? Let me know in the comments!",
                    "platform": "Instagram Reels/TikTok",
                    "duration": "30-60 seconds",
                    "hashtags": "#dayinthelife #morningroutine #contentcreator #lifestyle #vlog"
                },
                {
                    "script": "Tutorial How-To",
                    "content": "Hey everyone! Today I'm going to teach you how to [specific skill/topic]. First, you'll need [list materials]. Step 1: [detailed instruction]... Step 2: [detailed instruction]... And that's it! Try this at home and tag me in your results. Don't forget to follow for more tutorials!",
                    "platform": "Instagram Reels/YouTube Shorts",
                    "duration": "60-90 seconds",
                    "hashtags": "#tutorial #howto #diy #tips #learn #education"
                },
                {
                    "script": "Trending Topic Reaction",
                    "content": "Have you seen this trending topic about [topic]? I have some thoughts... [Share opinion] What do you think about this? Let me know in the comments! I'm curious to hear different perspectives. Follow for more hot takes!",
                    "platform": "Instagram Stories/TikTok",
                    "duration": "15-30 seconds",
                    "hashtags": "#trending #reaction #opinion #discussion #thoughts"
                },
                {
                    "script": "Behind-the-Scenes Content",
                    "content": "Behind the scenes of creating today's content! This is what really goes into [content type]... [Show process] It's not always as glamorous as it looks! What would you like to see more of? Comment below!",
                    "platform": "Instagram Stories/YouTube Shorts",
                    "duration": "30-45 seconds",
                    "hashtags": "#behindthescenes #bts #contentcreation #process #real"
                },
                {
                    "script": "Community Question",
                    "content": "Quick question for my amazing community: [Ask engaging question] I'm really curious about your experiences with this. Drop your answers in the comments and let's start a conversation! Don't forget to follow for more community discussions!",
                    "platform": "Instagram Post/Story",
                    "duration": "20-30 seconds",
                    "hashtags": "#community #question #discussion #engagement #conversation"
                }
            ]
        }
    
    async def generate_strategies(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        recommendation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate strategies using rule-based approach instead of AI
        """
        try:
            logger.info(f"🤖 NON-AI STRATEGY GENERATION: Starting for influencer_id: {influencer_id}")
            
            # Get recommendation data
            recommendation_data = await self._get_recommendation_data(db, influencer_id, recommendation_id)
            if not recommendation_data:
                raise ValueError(f"No recommendation data found for influencer_id: {influencer_id}")
            
            # Analyze recommendation data to customize strategies
            user_level = recommendation_data.get('user_level', 'intermediate')
            platform_data = self._analyze_platform_data(recommendation_data)
            niche_data = self._analyze_niche_data(recommendation_data)
            
            # Generate customized strategies based on analysis
            strategies = self._generate_customized_strategies(
                user_level, platform_data, niche_data
            )
            
            # Generate personalized content scripts
            logger.info(f"📝 Generating personalized content scripts...")
            strategies['content_scripts'] = self._generate_personalized_content_scripts(
                user_level, platform_data, niche_data
            )
            
            # Enhance strategies with real links from DuckDuckGo
            logger.info(f"🔍 Enhancing strategies with real links from DuckDuckGo...")
            enhanced_strategies = await self._enhance_strategies_with_real_links(
                strategies, niche_data, platform_data, recommendation_data.get('location')
            )
            
            # Save strategies to database and generate download files
            logger.info(f"💾 Saving strategies to database...")
            summary = await self.save_strategies_to_db(
                db, influencer_id, recommendation_data['recommendation_id'], enhanced_strategies
            )
            
            # Prepare response with download links
            response_data = {
                'summary_id': summary.id,
                'strategies': enhanced_strategies,
                'download_links': summary.download_links or []
            }
            
            logger.info(f"✅ NON-AI strategies generated successfully for influencer_id: {influencer_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Error generating non-AI strategies: {str(e)}")
            raise
    
    def _analyze_platform_data(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze recommendation data to identify platform preferences"""
        content = str(recommendation_data.get('base_plan', '')) + str(recommendation_data.get('enhanced_plan', ''))
        
        platforms = {
            'instagram': 'instagram' in content.lower(),
            'tiktok': 'tiktok' in content.lower(),
            'youtube': 'youtube' in content.lower(),
            'twitter': 'twitter' in content.lower()
        }
        
        return {
            'primary_platform': max(platforms, key=platforms.get) if any(platforms.values()) else 'instagram',
            'platforms': platforms
        }
    
    def _analyze_niche_data(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze recommendation data to identify niche and content themes"""
        content = str(recommendation_data.get('base_plan', '')) + str(recommendation_data.get('enhanced_plan', ''))
        
        niches = {
            'fashion': 'fashion' in content.lower(),
            'lifestyle': 'lifestyle' in content.lower(),
            'business': 'business' in content.lower(),
            'education': 'education' in content.lower(),
            'fitness': 'fitness' in content.lower(),
            'food': 'food' in content.lower()
        }
        
        return {
            'primary_niche': max(niches, key=niches.get) if any(niches.values()) else 'lifestyle',
            'niches': niches
        }
    
    def _generate_customized_strategies(
        self, 
        user_level: str, 
        platform_data: Dict[str, Any], 
        niche_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate customized strategies based on user profile analysis"""
        
        # Get base templates
        strategies = {}
        
        for category, template_strategies in self.strategy_templates.items():
            # Customize strategies based on user level and platform
            customized_strategies = []
            
            for strategy in template_strategies:
                customized_strategy = strategy.copy()
                
                # Customize based on user level
                if user_level == 'beginner':
                    customized_strategy['implementation'] = f"Start with: {strategy['implementation']}"
                elif user_level == 'advanced':
                    customized_strategy['implementation'] = f"Advanced approach: {strategy['implementation']}"
                
                # Customize based on platform
                primary_platform = platform_data.get('primary_platform', 'instagram')
                if 'platform' in customized_strategy:
                    customized_strategy['platform'] = primary_platform.title()
                
                # Customize based on niche
                primary_niche = niche_data.get('primary_niche', 'lifestyle')
                if 'description' in customized_strategy:
                    customized_strategy['description'] = f"{strategy['description']} (optimized for {primary_niche} niche)"
                
                customized_strategies.append(customized_strategy)
            
            strategies[category] = customized_strategies
        
        return strategies
    
    async def _enhance_strategies_with_real_links(
        self, 
        strategies: Dict[str, Any], 
        niche_data: Dict[str, Any], 
        platform_data: Dict[str, Any],
        location_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enhance strategies with real links from DuckDuckGo search"""
        try:
            enhanced_strategies = strategies.copy()
            
            # Enhance influencer_collab with real influencer links
            if 'influencer_collab' in enhanced_strategies:
                enhanced_strategies['influencer_collab'] = await self._enhance_collaboration_links(
                    enhanced_strategies['influencer_collab'], niche_data, platform_data, location_data
                )
            
            # Enhance business_collab with real business links
            if 'business_collab' in enhanced_strategies:
                logger.info(f"🔍 Enhancing business_collab with location data: {location_data}")
                enhanced_strategies['business_collab'] = await self._enhance_business_links(
                    enhanced_strategies['business_collab'], niche_data, platform_data, location_data
                )
                logger.info(f"✅ Business links enhancement completed")
            
            return enhanced_strategies
            
        except Exception as e:
            logger.error(f"❌ Error enhancing strategies with real links: {str(e)}")
            return strategies  # Return original strategies if enhancement fails
    
    async def _enhance_collaboration_links(
        self, 
        collaboration_strategies: List[Dict], 
        niche_data: Dict[str, Any], 
        platform_data: Dict[str, Any],
        location_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Enhance collaboration strategies with real influencer links"""
        logger.info(f"🔍 Starting influencer collaboration links enhancement with {len(collaboration_strategies)} strategies")
        enhanced_strategies = []
        
        for strategy in collaboration_strategies:
            enhanced_strategy = strategy.copy()
            
            # Create item-specific search query for real influencers
            niche = niche_data.get('primary_niche', 'lifestyle')
            platform = platform_data.get('primary_platform', 'instagram')
            collaboration = strategy.get('collaboration', 'influencer collaboration')
            
            # Build item-specific search query based on collaboration type
            current_year = datetime.now().year
            if location_data and location_data.get('city_name'):
                city = location_data['city_name']
                country = location_data.get('country_name', '')
                # Create unique search query per influencer collaboration item
                search_query = f"{niche} {collaboration.lower()} {platform} {city} {country} {current_year}"
                logger.info(f"🌍 Item-specific influencer search: {search_query}")
            else:
                search_query = f"{niche} {collaboration.lower()} {platform} collaboration {current_year}"
                logger.info(f"🌐 Global item-specific influencer search: {search_query}")
            
            try:
                # Search for real influencer profiles with location context
                real_links = await self._search_duckduckgo_for_influencers(
                    search_query, niche, platform, location_data
                )
                
                # Add hyperlocal influencer searches (street/town level)
                if location_data and location_data.get('latitude') and location_data.get('longitude'):
                    hyperlocal_links = await self._search_hyperlocal_influencers(
                        niche, platform, location_data, collaboration
                    )
                    if hyperlocal_links:
                        real_links.extend(hyperlocal_links)
                        logger.info(f"🏘️ Added {len(hyperlocal_links)} hyperlocal influencer links")
                
                if real_links:
                    enhanced_strategy['real_links'] = real_links
                    enhanced_strategy['search_query'] = search_query
                    enhanced_strategy['location_context'] = location_data.get('city_name', 'Global') if location_data else 'Global'
                    logger.info(f"✅ Found {len(real_links)} total influencer links for: {search_query}")
                else:
                    enhanced_strategy['real_links'] = []
                    enhanced_strategy['search_query'] = search_query
                    enhanced_strategy['location_context'] = location_data.get('city_name', 'Global') if location_data else 'Global'
                    logger.warning(f"⚠️ No real links found for: {search_query}")
                    
            except Exception as e:
                logger.error(f"❌ Error searching for influencer links: {str(e)}")
                enhanced_strategy['real_links'] = []
                enhanced_strategy['search_query'] = search_query
                enhanced_strategy['location_context'] = location_data.get('city_name', 'Global') if location_data else 'Global'
            
            enhanced_strategies.append(enhanced_strategy)
        
        return enhanced_strategies
    
    async def _enhance_business_links(
        self, 
        business_strategies: List[Dict], 
        niche_data: Dict[str, Any], 
        platform_data: Dict[str, Any],
        location_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Enhance business strategies with location-based real business links"""
        logger.info(f"🔍 Starting business links enhancement with {len(business_strategies)} strategies")
        logger.info(f"📍 Location data: {location_data}")
        enhanced_strategies = []
        
        for strategy in business_strategies:
            enhanced_strategy = strategy.copy()
            
            # Create location-based search query for real businesses
            niche = niche_data.get('primary_niche', 'lifestyle')
            business_type = strategy.get('type', 'brand partnership')
            opportunity = strategy.get('opportunity', 'business collaboration')
            
            # Build item-specific search query based on opportunity and type
            current_year = datetime.now().year
            if location_data and location_data.get('city_name'):
                city = location_data['city_name']
                country = location_data.get('country_name', '')
                # Create unique search query per business item with current year
                search_query = f"{niche} {business_type.lower()} {opportunity.lower()} {city} {country} collaboration {current_year}"
                logger.info(f"🌍 Item-specific search: {search_query}")
            else:
                search_query = f"{niche} {business_type.lower()} {opportunity.lower()} partnership opportunities {current_year}"
                logger.info(f"🌐 Global item-specific search: {search_query}")
            
            try:
                # Search for real business websites with location context
                real_links = await self._search_duckduckgo_for_businesses(
                    search_query, niche, business_type, location_data
                )
                
                # Add hyperlocal business searches (street/town level)
                if location_data and location_data.get('latitude') and location_data.get('longitude'):
                    hyperlocal_links = await self._search_hyperlocal_businesses(
                        niche, business_type, location_data, opportunity
                    )
                    if hyperlocal_links:
                        real_links.extend(hyperlocal_links)
                        logger.info(f"🏘️ Added {len(hyperlocal_links)} hyperlocal business links")
                
                if real_links:
                    enhanced_strategy['real_links'] = real_links
                    enhanced_strategy['search_query'] = search_query
                    enhanced_strategy['location_context'] = location_data.get('city_name', 'Global') if location_data else 'Global'
                    logger.info(f"✅ Found {len(real_links)} total business links for: {search_query}")
                else:
                    enhanced_strategy['real_links'] = []
                    enhanced_strategy['search_query'] = search_query
                    enhanced_strategy['location_context'] = location_data.get('city_name', 'Global') if location_data else 'Global'
                    logger.warning(f"⚠️ No real links found for: {search_query}")
                    
            except Exception as e:
                logger.error(f"❌ Error searching for business links: {str(e)}")
                enhanced_strategy['real_links'] = []
                enhanced_strategy['search_query'] = search_query
                enhanced_strategy['location_context'] = location_data.get('city_name', 'Global') if location_data else 'Global'
            
            enhanced_strategies.append(enhanced_strategy)
        
        return enhanced_strategies
    
    async def _search_duckduckgo_for_influencers(
        self,
        search_query: str,
        niche: str,
        platform: str,
        location_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Search DuckDuckGo for real influencer profiles"""
        try:
            # Add current year to influencer search queries
            current_year = datetime.now().year
            enhanced_query = f"{search_query} {current_year}"
            # Use DuckDuckGo MCP server to search for influencers
            search_results = await self._perform_duckduckgo_search(enhanced_query)

            real_links = []
            if search_results:
                for result in search_results[:3]:  # Limit to top 3 results
                    if result.get('url') and self._is_relevant_influencer_link(result['url'], platform):
                        real_links.append({
                            'name': result.get('title', 'Influencer Profile'),
                            'url': result['url'],
                            'description': result.get('body', ''),
                            'platform': platform,
                            'relevance': 'High' if niche.lower() in result.get('title', '').lower() else 'Medium'
                        })
            else:
                # Fallback to curated real links
                logger.info(f"🔄 Using curated real links for influencers: {search_query}")
                curated_links = self._get_curated_real_links(search_query, niche, platform, location_data)
                for link in curated_links[:3]:
                    real_links.append({
                        'name': link['title'],
                        'url': link['url'],
                        'description': link['body'],
                        'platform': platform,
                        'relevance': 'High'
                    })

            return real_links

        except Exception as e:
            logger.error(f"❌ Error in DuckDuckGo search for influencers: {str(e)}")
            # Fallback to curated links
            logger.info(f"🔄 Using curated real links as fallback for influencers: {search_query}")
            curated_links = self._get_curated_real_links(search_query, niche, platform)
            real_links = []
            for link in curated_links[:3]:
                real_links.append({
                    'name': link['title'],
                    'url': link['url'],
                    'description': link['body'],
                    'platform': platform,
                    'relevance': 'High'
                })
            return real_links
    
    async def _search_duckduckgo_for_businesses(
        self,
        search_query: str,
        niche: str,
        business_type: str,
        location_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Search DuckDuckGo for location-based real business websites"""
        try:
            # Enhanced search query with location information and current year
            current_year = datetime.now().year
            enhanced_query = f"{search_query} {current_year}"
            if location_data:
                city = location_data.get('city_name', '')
                country = location_data.get('country_name', '')
                if city and country:
                    enhanced_query = f"{search_query} near {city} {country} {current_year}"
                elif city:
                    enhanced_query = f"{search_query} near {city} {current_year}"
                elif country:
                    enhanced_query = f"{search_query} in {country} {current_year}"
            
            logger.info(f"🔍 Location-based business search: {enhanced_query}")
            
            # Use DuckDuckGo MCP server to search for businesses
            search_results = await self._perform_duckduckgo_search(enhanced_query)

            real_links = []
            if search_results:
                for result in search_results[:3]:  # Limit to top 3 results
                    if result.get('url') and self._is_relevant_business_link(result['url'], business_type):
                        # Add location context to the link
                        location_context = ""
                        if location_data and location_data.get('city_name'):
                            location_context = f" in {location_data['city_name']}"
                        
                        real_links.append({
                            'name': result.get('title', 'Business Website'),
                            'url': result['url'],
                            'description': result.get('body', ''),
                            'business_type': business_type,
                            'location': location_context.strip(),
                            'relevance': 'High' if niche.lower() in result.get('title', '').lower() else 'Medium'
                        })
            else:
                # Fallback to curated real links with location context
                logger.info(f"🔄 Using curated real links for businesses: {search_query}")
                curated_links = self._get_curated_real_links(search_query, niche, 'business', location_data)
                for link in curated_links[:3]:
                    real_links.append({
                        'name': link['title'],
                        'url': link['url'],
                        'description': link['body'],
                        'business_type': business_type,
                        'location': link.get('location', ''),
                        'relevance': 'High'
                    })

            return real_links

        except Exception as e:
            logger.error(f"❌ Error in DuckDuckGo search for businesses: {str(e)}")
            # Fallback to curated links
            logger.info(f"🔄 Using curated real links as fallback for businesses: {search_query}")
            curated_links = self._get_curated_real_links(search_query, niche, 'business', location_data)
            real_links = []
            for link in curated_links[:3]:
                real_links.append({
                    'name': link['title'],
                    'url': link['url'],
                    'description': link['body'],
                    'business_type': business_type,
                    'location': link.get('location', ''),
                    'relevance': 'High'
                })
            return real_links

    async def _search_hyperlocal_businesses(
        self,
        niche: str,
        business_type: str,
        location_data: Dict[str, Any],
        opportunity: str = "business collaboration"
    ) -> List[Dict[str, str]]:
        """Search for hyperlocal businesses at street/town level using coordinates"""
        try:
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')
            city = location_data.get('city_name', '')
            region = location_data.get('region_name', '')
            
            if not latitude or not longitude:
                logger.warning("⚠️ No coordinates available for hyperlocal search")
                return []
            
            # Create item-specific hyperlocal search queries using coordinates and local area names
            current_year = datetime.now().year
            hyperlocal_queries = [
                f"{niche} {business_type.lower()} {opportunity.lower()} near me {city} {region} {current_year}",
                f"local {niche} {business_type.lower()} {city} {region} {current_year}",
                f"{niche} {opportunity.lower()} {city} {region} collaboration {current_year}",
                f"small {niche} {business_type.lower()} {city} {region} {current_year}",
                f"independent {niche} {business_type.lower()} {city} {region} {current_year}"
            ]
            
            logger.info(f"🏘️ Searching hyperlocal businesses at coordinates: {latitude}, {longitude}")
            
            hyperlocal_links = []
            for query in hyperlocal_queries[:2]:  # Limit to 2 hyperlocal searches
                try:
                    search_results = await self._perform_duckduckgo_search(query)
                    if search_results:
                        for result in search_results[:1]:  # Take 1 result per query
                            if result.get('url') and self._is_relevant_business_link(result['url'], business_type):
                                hyperlocal_links.append({
                                    'name': result.get('title', 'Local Business'),
                                    'url': result['url'],
                                    'description': result.get('body', ''),
                                    'business_type': business_type,
                                    'relevance': 'High',
                                    'search_type': 'hyperlocal',
                                    'location': f"near {city}" if city else "local area",
                                    'coordinates': f"{latitude}, {longitude}"
                                })
                                break  # Only take one result per query
                except Exception as e:
                    logger.warning(f"⚠️ Hyperlocal search failed for query '{query}': {str(e)}")
                    continue
            
            # If no hyperlocal results found, create curated hyperlocal links
            if not hyperlocal_links:
                logger.info(f"🔄 Creating curated hyperlocal links for {city}")
                curated_hyperlocal = self._get_curated_hyperlocal_links(niche, business_type, location_data, opportunity)
                hyperlocal_links.extend(curated_hyperlocal)
            
            logger.info(f"🏘️ Found {len(hyperlocal_links)} hyperlocal business links")
            return hyperlocal_links

        except Exception as e:
            logger.error(f"❌ Error in hyperlocal business search: {str(e)}")
            return []

    def _get_curated_hyperlocal_links(
        self, 
        niche: str, 
        business_type: str, 
        location_data: Dict[str, Any],
        opportunity: str = "business collaboration"
    ) -> List[Dict[str, str]]:
        """Get curated hyperlocal business links based on coordinates"""
        city = location_data.get('city_name', '')
        region = location_data.get('region_name', '')
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        
        # Create Google Maps and local business directory links
        hyperlocal_links = []
        
        if city and latitude and longitude:
            current_year = datetime.now().year
            # Google Maps search for local businesses (item-specific)
            maps_query = f"{niche}+{business_type.lower().replace(' ', '+')}+{opportunity.lower().replace(' ', '+')}+{city.replace(' ', '+')}+{current_year}"
            hyperlocal_links.append({
                'name': f'Local {niche.title()} {business_type} - Google Maps',
                'url': f'https://www.google.com/maps/search/{maps_query}/@{latitude},{longitude},15z',
                'description': f'Find {niche} {business_type.lower()} near your location in {city}',
                'business_type': business_type,
                'relevance': 'High',
                'search_type': 'hyperlocal',
                'location': f"near {city}",
                'coordinates': f"{latitude}, {longitude}"
            })
            
            # Local business directory search (item-specific)
            directory_query = f"{niche}+{business_type.lower().replace(' ', '+')}+{opportunity.lower().replace(' ', '+')}+{city.replace(' ', '+')}+{region.replace(' ', '+')}+{current_year}"
            hyperlocal_links.append({
                'name': f'Local {niche.title()} {business_type} Directory - {city}',
                'url': f'https://www.google.com/search?q={directory_query}',
                'description': f'Discover local {niche} {business_type.lower()} and {opportunity.lower()} in {city}, {region}',
                'business_type': business_type,
                'relevance': 'High',
                'search_type': 'hyperlocal',
                'location': f"in {city}, {region}",
                'coordinates': f"{latitude}, {longitude}"
            })
        
        return hyperlocal_links
    
    async def _search_hyperlocal_influencers(
        self,
        niche: str,
        platform: str,
        location_data: Dict[str, Any],
        collaboration: str = "influencer collaboration"
    ) -> List[Dict[str, str]]:
        """Search for hyperlocal influencers at street/town level using coordinates"""
        try:
            latitude = location_data.get('latitude')
            longitude = location_data.get('longitude')
            city = location_data.get('city_name', '')
            region = location_data.get('region_name', '')
            
            if not latitude or not longitude:
                logger.warning("⚠️ No coordinates available for hyperlocal influencer search")
                return []
            
            # Create item-specific hyperlocal search queries using coordinates and local area names
            current_year = datetime.now().year
            hyperlocal_queries = [
                f"{niche} {collaboration.lower()} {platform} near me {city} {region} {current_year}",
                f"local {niche} {platform} influencers {city} {region} {current_year}",
                f"{niche} {collaboration.lower()} {city} {region} {platform} {current_year}",
                f"small {niche} {platform} influencers {city} {region} {current_year}",
                f"independent {niche} {platform} creators {city} {region} {current_year}"
            ]
            
            logger.info(f"🏘️ Searching hyperlocal influencers at coordinates: {latitude}, {longitude}")
            
            hyperlocal_links = []
            for query in hyperlocal_queries[:2]:  # Limit to 2 hyperlocal searches
                try:
                    search_results = await self._perform_duckduckgo_search(query)
                    if search_results:
                        for result in search_results[:1]:  # Take 1 result per query
                            if result.get('url') and self._is_relevant_influencer_link(result['url'], platform):
                                hyperlocal_links.append({
                                    'name': result.get('title', 'Local Influencer'),
                                    'url': result['url'],
                                    'description': result.get('body', ''),
                                    'platform': platform,
                                    'relevance': 'High',
                                    'search_type': 'hyperlocal',
                                    'location': f"near {city}" if city else "local area",
                                    'coordinates': f"{latitude}, {longitude}"
                                })
                                break  # Only take one result per query
                except Exception as e:
                    logger.warning(f"⚠️ Hyperlocal influencer search failed for query '{query}': {str(e)}")
                    continue
            
            # If no hyperlocal results found, create curated hyperlocal links
            if not hyperlocal_links:
                logger.info(f"🔄 Creating curated hyperlocal influencer links for {city}")
                curated_hyperlocal = self._get_curated_hyperlocal_influencer_links(niche, platform, location_data, collaboration)
                hyperlocal_links.extend(curated_hyperlocal)
            
            logger.info(f"🏘️ Found {len(hyperlocal_links)} hyperlocal influencer links")
            return hyperlocal_links

        except Exception as e:
            logger.error(f"❌ Error in hyperlocal influencer search: {str(e)}")
            return []
    
    def _get_curated_hyperlocal_influencer_links(
        self, 
        niche: str, 
        platform: str, 
        location_data: Dict[str, Any],
        collaboration: str = "influencer collaboration"
    ) -> List[Dict[str, str]]:
        """Get curated hyperlocal influencer links based on coordinates"""
        city = location_data.get('city_name', '')
        region = location_data.get('region_name', '')
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        
        # Create Instagram and TikTok local influencer directory links
        hyperlocal_links = []
        
        if city and latitude and longitude:
            current_year = datetime.now().year
            # Instagram local influencer search (item-specific)
            instagram_query = f"{niche}+{platform.lower()}+{collaboration.lower().replace(' ', '+')}+{city.replace(' ', '+')}+{current_year}"
            hyperlocal_links.append({
                'name': f'Local {niche.title()} {platform.title()} Influencers - {city}',
                'url': f'https://www.instagram.com/explore/tags/{niche.lower()}{city.lower().replace(" ", "")}/',
                'description': f'Find local {niche} {platform} influencers and creators in {city}',
                'platform': platform,
                'relevance': 'High',
                'search_type': 'hyperlocal',
                'location': f"in {city}",
                'coordinates': f"{latitude}, {longitude}"
            })
            
            # TikTok local creator search (item-specific)
            tiktok_query = f"{niche}+{platform.lower()}+{collaboration.lower().replace(' ', '+')}+{city.replace(' ', '+')}+{region.replace(' ', '+')}+{current_year}"
            hyperlocal_links.append({
                'name': f'Local {niche.title()} {platform.title()} Creators - {city}',
                'url': f'https://www.tiktok.com/search?q={tiktok_query}',
                'description': f'Discover local {niche} {platform} creators and influencers in {city}, {region}',
                'platform': platform,
                'relevance': 'High',
                'search_type': 'hyperlocal',
                'location': f"in {city}, {region}",
                'coordinates': f"{latitude}, {longitude}"
            })
        
        return hyperlocal_links
    
    def _extract_collaboration_type_from_query(self, query: str) -> str:
        """Extract collaboration type from search query for item-specific links"""
        query_lower = query.lower()
        
        if 'cross-promotion' in query_lower or 'cross promotion' in query_lower:
            return 'cross_promotion'
        elif 'content collaboration' in query_lower or 'content collab' in query_lower:
            return 'content_collaboration'
        elif 'brand partnership' in query_lower or 'brand collab' in query_lower:
            return 'brand_partnership'
        elif 'influencer collaboration' in query_lower or 'influencer collab' in query_lower:
            return 'influencer_collaboration'
        elif 'joint venture' in query_lower or 'joint venture' in query_lower:
            return 'joint_venture'
        else:
            return 'general_collaboration'
    
    def _get_fashion_influencer_links(self, collaboration_type: str, platform: str, location_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Get item-specific fashion influencer links based on collaboration type"""
        links = []
        
        if collaboration_type == 'cross_promotion':
            links = [
                {
                    'title': 'Fashion Cross-Promotion Network',
                    'url': 'https://www.instagram.com/explore/tags/fashioncrosspromotion/',
                    'body': 'Connect with fashion influencers for cross-promotion opportunities'
                },
                {
                    'title': 'Fashion Influencer Exchange',
                    'url': 'https://influence.co/categories/fashion/cross-promotion',
                    'body': 'Find fashion influencers for mutual promotion and content sharing'
                },
                {
                    'title': 'Fashion Creator Network',
                    'url': 'https://creator.co/categories/fashion/collaboration',
                    'body': 'Join fashion creator network for cross-promotion partnerships'
                }
            ]
        elif collaboration_type == 'content_collaboration':
            links = [
                {
                    'title': 'Fashion Content Creator Hub',
                    'url': 'https://www.instagram.com/explore/tags/fashioncontent/',
                    'body': 'Collaborate with fashion content creators for joint projects'
                },
                {
                    'title': 'Fashion Creator Studio',
                    'url': 'https://aspireiq.com/creators/fashion/content',
                    'body': 'Connect with fashion creators for content collaboration'
                },
                {
                    'title': 'Fashion Content Network',
                    'url': 'https://creator.co/categories/fashion/content',
                    'body': 'Find fashion creators for content collaboration projects'
                }
            ]
        elif collaboration_type == 'brand_partnership':
            links = [
                {
                    'title': 'Fashion Brand Partnership Hub',
                    'url': 'https://influence.co/categories/fashion/brands',
                    'body': 'Connect with fashion brands for partnership opportunities'
                },
                {
                    'title': 'Fashion Brand Network',
                    'url': 'https://aspireiq.com/brands/fashion',
                    'body': 'Find fashion brands looking for influencer partnerships'
                },
                {
                    'title': 'Fashion Partnership Directory',
                    'url': 'https://creator.co/categories/fashion/brands',
                    'body': 'Discover fashion brands for collaboration opportunities'
                }
            ]
        elif collaboration_type == 'influencer_collaboration':
            links = [
                {
                    'title': 'Fashion Influencer Directory',
                    'url': 'https://www.instagram.com/explore/tags/fashioninfluencer/',
                    'body': 'Find fashion influencers for collaboration opportunities'
                },
                {
                    'title': 'Fashion Creator Network',
                    'url': 'https://influence.co/categories/fashion',
                    'body': 'Connect with verified fashion influencers and creators'
                },
                {
                    'title': 'Fashion Influencer Hub',
                    'url': 'https://aspireiq.com/creators/fashion',
                    'body': 'Discover fashion influencers for brand partnerships'
                }
            ]
        elif collaboration_type == 'joint_venture':
            links = [
                {
                    'title': 'Fashion Joint Venture Network',
                    'url': 'https://creator.co/categories/fashion/ventures',
                    'body': 'Find fashion creators for joint business ventures'
                },
                {
                    'title': 'Fashion Business Network',
                    'url': 'https://influence.co/categories/fashion/business',
                    'body': 'Connect with fashion entrepreneurs for joint ventures'
                },
                {
                    'title': 'Fashion Venture Hub',
                    'url': 'https://aspireiq.com/creators/fashion/ventures',
                    'body': 'Discover fashion creators for business partnerships'
                }
            ]
        else:  # general_collaboration
            links = [
                {
                    'title': 'Fashion Influencer Network',
                    'url': 'https://www.instagram.com/explore/tags/fashion/',
                    'body': 'Connect with fashion influencers for various collaboration opportunities'
                },
                {
                    'title': 'Fashion Creator Hub',
                    'url': 'https://creator.co/categories/fashion',
                    'body': 'Find fashion creators for collaboration and partnerships'
                },
                {
                    'title': 'Fashion Collaboration Network',
                    'url': 'https://influence.co/categories/fashion/collaboration',
                    'body': 'Discover fashion influencers for collaboration opportunities'
                }
            ]
        
        # Add location-specific links if available
        if location_data and location_data.get('city_name'):
            city = location_data['city_name']
            location_links = [
                {
                    'title': f'Local Fashion Influencers - {city}',
                    'url': f'https://www.instagram.com/explore/tags/fashion{city.lower().replace(" ", "")}/',
                    'body': f'Find local fashion influencers in {city} for collaboration'
                }
            ]
            links.extend(location_links)
        
        return links[:3]  # Return maximum 3 links per item
    
    def _get_lifestyle_influencer_links(self, collaboration_type: str, platform: str, location_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Get item-specific lifestyle influencer links based on collaboration type"""
        links = []
        
        if collaboration_type == 'cross_promotion':
            links = [
                {
                    'title': 'Lifestyle Cross-Promotion Network',
                    'url': 'https://www.instagram.com/explore/tags/lifestylecrosspromotion/',
                    'body': 'Connect with lifestyle influencers for cross-promotion opportunities'
                },
                {
                    'title': 'Lifestyle Influencer Exchange',
                    'url': 'https://influence.co/categories/lifestyle/cross-promotion',
                    'body': 'Find lifestyle influencers for mutual promotion and content sharing'
                },
                {
                    'title': 'Lifestyle Creator Network',
                    'url': 'https://creator.co/categories/lifestyle/collaboration',
                    'body': 'Join lifestyle creator network for cross-promotion partnerships'
                }
            ]
        elif collaboration_type == 'content_collaboration':
            links = [
                {
                    'title': 'Lifestyle Content Creator Hub',
                    'url': 'https://www.instagram.com/explore/tags/lifestylecontent/',
                    'body': 'Collaborate with lifestyle content creators for joint projects'
                },
                {
                    'title': 'Lifestyle Creator Studio',
                    'url': 'https://aspireiq.com/creators/lifestyle/content',
                    'body': 'Connect with lifestyle creators for content collaboration'
                },
                {
                    'title': 'Lifestyle Content Network',
                    'url': 'https://creator.co/categories/lifestyle/content',
                    'body': 'Find lifestyle creators for content collaboration projects'
                }
            ]
        elif collaboration_type == 'brand_partnership':
            links = [
                {
                    'title': 'Lifestyle Brand Partnership Hub',
                    'url': 'https://influence.co/categories/lifestyle/brands',
                    'body': 'Connect with lifestyle brands for partnership opportunities'
                },
                {
                    'title': 'Lifestyle Brand Network',
                    'url': 'https://aspireiq.com/brands/lifestyle',
                    'body': 'Find lifestyle brands looking for influencer partnerships'
                },
                {
                    'title': 'Lifestyle Partnership Directory',
                    'url': 'https://creator.co/categories/lifestyle/brands',
                    'body': 'Discover lifestyle brands for collaboration opportunities'
                }
            ]
        elif collaboration_type == 'influencer_collaboration':
            links = [
                {
                    'title': 'Lifestyle Influencer Directory',
                    'url': 'https://www.instagram.com/explore/tags/lifestyle/',
                    'body': 'Find lifestyle influencers for collaboration opportunities'
                },
                {
                    'title': 'Lifestyle Creator Network',
                    'url': 'https://influence.co/categories/lifestyle',
                    'body': 'Connect with verified lifestyle influencers and creators'
                },
                {
                    'title': 'Lifestyle Influencer Hub',
                    'url': 'https://aspireiq.com/creators/lifestyle',
                    'body': 'Discover lifestyle influencers for brand partnerships'
                }
            ]
        elif collaboration_type == 'joint_venture':
            links = [
                {
                    'title': 'Lifestyle Joint Venture Network',
                    'url': 'https://creator.co/categories/lifestyle/ventures',
                    'body': 'Find lifestyle creators for joint business ventures'
                },
                {
                    'title': 'Lifestyle Business Network',
                    'url': 'https://influence.co/categories/lifestyle/business',
                    'body': 'Connect with lifestyle entrepreneurs for joint ventures'
                },
                {
                    'title': 'Lifestyle Venture Hub',
                    'url': 'https://aspireiq.com/creators/lifestyle/ventures',
                    'body': 'Discover lifestyle creators for business partnerships'
                }
            ]
        else:  # general_collaboration
            links = [
                {
                    'title': 'Lifestyle Influencer Network',
                    'url': 'https://www.instagram.com/explore/tags/lifestyle/',
                    'body': 'Connect with lifestyle influencers for various collaboration opportunities'
                },
                {
                    'title': 'Lifestyle Creator Hub',
                    'url': 'https://creator.co/categories/lifestyle',
                    'body': 'Find lifestyle creators for collaboration and partnerships'
                },
                {
                    'title': 'Lifestyle Collaboration Network',
                    'url': 'https://influence.co/categories/lifestyle/collaboration',
                    'body': 'Discover lifestyle influencers for collaboration opportunities'
                }
            ]
        
        # Add location-specific links if available
        if location_data and location_data.get('city_name'):
            city = location_data['city_name']
            location_links = [
                {
                    'title': f'Local Lifestyle Influencers - {city}',
                    'url': f'https://www.instagram.com/explore/tags/lifestyle{city.lower().replace(" ", "")}/',
                    'body': f'Find local lifestyle influencers in {city} for collaboration'
                }
            ]
            links.extend(location_links)
        
        return links[:3]  # Return maximum 3 links per item
    
    async def _perform_duckduckgo_search(self, query: str) -> List[Dict[str, str]]:
        """Perform DuckDuckGo search using real DuckDuckGo API with rate limiting and caching"""
        try:
            # Check cache first to avoid unnecessary API calls
            cache_key = f"ddg_search_{hash(query)}"
            if cache_key in self.search_cache:
                logger.info(f"📋 Using cached search results for: {query}")
                return self.search_cache[cache_key]
            
            
            # Use the DuckDuckGo MCP server for real search results
            from app.services.mcp_client import MCPClient
            
            mcp_client = MCPClient()
            
            logger.info(f"🔍 Making DuckDuckGo search request for: {query}")
            
            # Perform real search using DuckDuckGo
            search_results = await mcp_client.call_mcp_server(
                "duckduckgo-search",
                "duckduckgo_search_web", 
                {"query": query, "limit": 3}
            )
            
            if search_results and 'results' in search_results:
                results = []
                for result in search_results['results']:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'body': result.get('snippet', '')
                    })
                
                # Cache the results to avoid repeated API calls
                self.search_cache[cache_key] = results
                logger.info(f"✅ DuckDuckGo search completed: {len(results)} real results for query: {query}")
                return results
            else:
                logger.warning(f"⚠️ No results from DuckDuckGo search for query: {query}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error performing DuckDuckGo search: {str(e)}")
            # Fallback to curated results if real search fails
            logger.info(f"🔄 Falling back to curated results for query: {query}")
            return []
    
    def _get_curated_real_links(self, query: str, niche: str, platform: str, location_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Get curated real, live links for collaboration opportunities with location context"""
        # Real, live links for influencer collaboration - ITEM-SPECIFIC
        if 'influencer' in query.lower():
            # Extract collaboration type from query for item-specific links
            collaboration_type = self._extract_collaboration_type_from_query(query)
            
            if 'fashion' in niche.lower():
                return self._get_fashion_influencer_links(collaboration_type, platform, location_data)
            elif 'lifestyle' in niche.lower():
                return self._get_lifestyle_influencer_links(collaboration_type, platform, location_data)
            else:
                return [
                    {
                        'title': 'Instagram Explore - Influencers',
                        'url': 'https://www.instagram.com/explore/',
                        'body': 'Discover trending influencers and creators on Instagram'
                    },
                    {
                        'title': 'TikTok Creator Marketplace',
                        'url': 'https://www.tiktok.com/business/en/creator-marketplace',
                        'body': 'Connect with TikTok creators for brand collaborations'
                    },
                    {
                        'title': 'YouTube Creator Hub',
                        'url': 'https://www.youtube.com/creators/',
                        'body': 'Find YouTube creators and influencers for partnerships'
                    }
                ]
        
        # Real, live links for business collaboration
        elif 'brand' in query.lower() or 'business' in query.lower():
            # Get location context for business links
            location_context = ""
            if location_data and location_data.get('city_name'):
                city = location_data['city_name']
                country = location_data.get('country_name', '')
                location_context = f" in {city}, {country}" if country else f" in {city}"
            
            if 'fashion' in niche.lower():
                # Location-specific fashion business links
                if location_data and location_data.get('city_name'):
                    city = location_data['city_name']
                    return [
                        {
                            'title': f'Fashion Brands in {city} - Local Directory',
                            'url': f'https://www.google.com/search?q=fashion+brands+{city.replace(" ", "+")}',
                            'body': f'Discover local fashion brands and retailers in {city} for collaboration opportunities',
                            'location': f' in {city}'
                        },
                        {
                            'title': f'{city} Fashion Week & Events',
                            'url': f'https://www.google.com/search?q={city.replace(" ", "+")}+fashion+week+events',
                            'body': f'Connect with fashion brands during {city} fashion events and shows',
                            'location': f' in {city}'
                        },
                        {
                            'title': f'Fashion Boutiques & Stores in {city}',
                            'url': f'https://www.google.com/search?q=fashion+boutiques+{city.replace(" ", "+")}',
                            'body': f'Find local fashion boutiques and stores in {city} for partnership opportunities',
                            'location': f' in {city}'
                        }
                    ]
                else:
                    return [
                        {
                            'title': f'Fashion Brand Partnership Opportunities{location_context}',
                            'url': 'https://www.businessoffashion.com/',
                            'body': f'Connect with fashion brands and industry professionals{location_context}',
                            'location': location_context
                        },
                        {
                            'title': f'Fashion Week Network{location_context}',
                            'url': 'https://www.fashionweek.com/',
                            'body': f'Partner with fashion brands during fashion week events{location_context}',
                            'location': location_context
                        },
                        {
                            'title': f'Style Coalition - Fashion Brands{location_context}',
                            'url': 'https://stylecoalition.com/',
                            'body': f'Collaborate with fashion brands and retailers{location_context}',
                            'location': location_context
                        }
                    ]
            elif 'lifestyle' in niche.lower():
                # Location-specific lifestyle business links
                if location_data and location_data.get('city_name'):
                    city = location_data['city_name']
                    return [
                        {
                            'title': f'Lifestyle Brands in {city} - Local Directory',
                            'url': f'https://www.google.com/search?q=lifestyle+brands+{city.replace(" ", "+")}',
                            'body': f'Discover local lifestyle brands and wellness businesses in {city} for collaboration',
                            'location': f' in {city}'
                        },
                        {
                            'title': f'{city} Wellness & Fitness Centers',
                            'url': f'https://www.google.com/search?q=wellness+centers+{city.replace(" ", "+")}',
                            'body': f'Connect with wellness and fitness businesses in {city} for partnerships',
                            'location': f' in {city}'
                        },
                        {
                            'title': f'Local Restaurants & Cafes in {city}',
                            'url': f'https://www.google.com/search?q=restaurants+cafes+{city.replace(" ", "+")}',
                            'body': f'Find local restaurants and cafes in {city} for food and lifestyle collaborations',
                            'location': f' in {city}'
                        }
                    ]
                else:
                    return [
                        {
                            'title': f'Lifestyle Brand Partnerships{location_context}',
                            'url': 'https://www.instagram.com/business/',
                            'body': f'Connect with lifestyle brands through Instagram Business{location_context}',
                            'location': location_context
                        },
                        {
                            'title': f'Wellness Brand Network{location_context}',
                            'url': 'https://www.wellnessbrands.com/',
                            'body': f'Partner with wellness and lifestyle brands{location_context}',
                            'location': location_context
                        },
                        {
                            'title': f'Home & Lifestyle Brands{location_context}',
                            'url': 'https://www.houzz.com/professionals',
                            'body': f'Collaborate with home and lifestyle service providers{location_context}',
                            'location': location_context
                        }
                    ]
            else:
                return [
                    {
                        'title': f'Brand Partnership Directory{location_context}',
                        'url': 'https://www.brandpartnerships.com/',
                        'body': f'Find brand partnership opportunities across industries{location_context}',
                        'location': location_context
                    },
                    {
                        'title': f'Influencer Marketing Hub{location_context}',
                        'url': 'https://influencermarketinghub.com/',
                        'body': f'Connect with brands looking for influencer partnerships{location_context}',
                        'location': location_context
                    },
                    {
                        'title': f'Creator Economy Network{location_context}',
                        'url': 'https://www.creatoreconomy.com/',
                        'body': f'Discover business opportunities in the creator economy{location_context}',
                        'location': location_context
                    }
                ]
        else:
            return []
    
    def _is_relevant_influencer_link(self, url: str, platform: str) -> bool:
        """Check if URL is relevant for influencer collaboration"""
        platform_domains = {
            'instagram': ['instagram.com', 'instagr.am'],
            'tiktok': ['tiktok.com', 'vm.tiktok.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'twitter': ['twitter.com', 'x.com']
        }
        
        if platform in platform_domains:
            return any(domain in url.lower() for domain in platform_domains[platform])
        return True  # Accept all URLs if platform not specified
    
    def _is_relevant_business_link(self, url: str, business_type: str) -> bool:
        """Check if URL is relevant for business collaboration"""
        # Filter out social media platforms for business links
        social_platforms = ['instagram.com', 'tiktok.com', 'youtube.com', 'twitter.com', 'facebook.com']
        return not any(platform in url.lower() for platform in social_platforms)
    
    async def _get_recommendation_data(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        recommendation_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Get recommendation data from database including location information"""
        # First, resolve influencer_id to user_id
        user_query = select(Influencer.user_id).where(Influencer.id == influencer_id)
        user_result = await db.execute(user_query)
        user_id = user_result.scalar_one_or_none()
        
        if not user_id:
            logger.error(f"No user found for influencer_id: {influencer_id}")
            return None
        
        # Get location data for the influencer (get first primary location)
        location_query = select(InfluencerOperationalLocation).where(
            InfluencerOperationalLocation.influencer_id == influencer_id,
            InfluencerOperationalLocation.is_primary == True
        ).limit(1)
        location_result = await db.execute(location_query)
        location = location_result.scalar_one_or_none()
        
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
        
        # Build location data
        location_data = None
        if location:
            location_data = {
                'city_name': location.city_name,
                'region_name': location.region_name,
                'country_name': location.country_name,
                'country_code': location.country_code,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude),
                'postcode': location.postcode,
                'time_zone': location.time_zone
            }
            logger.info(f"📍 Location data found: {location.city_name}, {location.country_name}")
        else:
            logger.warning(f"⚠️ No location data found for influencer_id: {influencer_id}")
        
        return {
            'id': recommendation.id,
            'recommendation_id': recommendation.id,
            'influencer_id': influencer_id,
            'user_id': user_id,
            'user_level': getattr(recommendation, 'user_level', 'intermediate'),
            'base_plan': recommendation.base_plan,
            'enhanced_plan': recommendation.enhanced_plan,
            'ai_insights': recommendation.ai_insights,
            'performance_goals': recommendation.performance_goals,
            'pricing_recommendations': recommendation.pricing_recommendations,
            'monthly_schedule': recommendation.monthly_schedule,
            'location': location_data
        }
    
    async def save_strategies_to_db(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        recommendation_id: int, 
        strategies: Dict[str, Any]
    ) -> InfluencerRecommendationSummaries:
        """Save generated strategies to database"""
        try:
            logger.info(f"💾 Saving non-AI strategies to database for influencer_id: {influencer_id}")
            
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
                
                # Generate download files and save links
                logger.info(f"📁 Generating download files for summary ID: {existing_summary.id}")
                download_links = await self.generate_download_files(strategies, existing_summary.id)
                existing_summary.download_links = download_links
                
                await db.commit()
                await db.refresh(existing_summary)
                logger.info(f"✅ Successfully updated existing summary with {len(download_links)} download files")
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
                
                # Generate download files and save links
                logger.info(f"📁 Generating download files for new summary ID: {new_summary.id}")
                download_links = await self.generate_download_files(strategies, new_summary.id)
                new_summary.download_links = download_links
                await db.commit()
                await db.refresh(new_summary)
                
                logger.info(f"✅ Successfully created new summary with ID: {new_summary.id} and {len(download_links)} download files")
                return new_summary
                
        except Exception as e:
            logger.error(f"❌ Database save error: {str(e)}")
            await db.rollback()
            raise e
    
    def _generate_personalized_content_scripts(self, user_level: str, platform_data: Dict[str, Any], niche_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate personalized content scripts using real influencer profile details"""
        niche = niche_data.get('primary_niche', 'lifestyle')
        platform = platform_data.get('primary_platform', 'instagram')
        
        # Generate personalized scripts based on niche and platform
        if niche.lower() == 'fashion':
            return self._generate_fashion_content_scripts(platform, user_level)
        elif niche.lower() == 'lifestyle':
            return self._generate_lifestyle_content_scripts(platform, user_level)
        elif niche.lower() == 'fitness':
            return self._generate_fitness_content_scripts(platform, user_level)
        else:
            return self._generate_general_content_scripts(platform, user_level)
    
    def _generate_fashion_content_scripts(self, platform: str, user_level: str) -> List[Dict[str, str]]:
        """Generate fashion-specific content scripts"""
        return [
            {
                "script": "Fashion OOTD (Outfit of the Day)",
                "content": f"""VIDEO SCRIPT: "5 Fashion Styling Secrets That Will Transform Your Look"

[SCENE 1: HOOK (0-3 seconds)
Visual: Eye-catching title card with bold text
Text Overlay: "5 Fashion Secrets That Changed Everything"
Narration: "Want to know the styling secrets that fashion influencers use every day?"

[SCENE 2: INTRODUCTION (3-8 seconds)
Visual: Person speaking to camera in stylish outfit
Text Overlay: "Hi, I'm [Your Name]"
Narration: "Hi there! I'm [Your Name], and today I'm sharing 5 game-changing fashion tips that will transform your style game."

[SCENE 3: TIP 1 (8-15 seconds)
Visual: Clean, minimal background with text overlay
Text Overlay: "Tip #1: Mix Textures"
Narration: "First tip: Mix textures for visual interest. Pair this amazing {self._get_fashion_item()} with {self._get_fashion_accessory()}. The contrast creates depth and sophistication."

[SCENE 4: TIP 2 (15-22 seconds)
Visual: Showing outfit details and styling
Text Overlay: "Tip #2: Define Your Waist"
Narration: "Second tip: Always define your waist. This {self._get_fashion_color()} piece adds {self._get_fashion_style_tip()} to your look. The key is {self._get_fashion_styling_tip()}."

[SCENE 5: TIP 3 (22-29 seconds)
Visual: Different styling options
Text Overlay: "Tip #3: Accessorize Strategically"
Narration: "Third tip: Accessorize strategically. Your {self._get_fashion_category()} piece becomes a statement when styled right. Less is more, but make it count."

[SCENE 6: TIP 4 (29-36 seconds)
Visual: Before and after styling comparison
Text Overlay: "Tip #4: Play with Proportions"
Narration: "Fourth tip: Play with proportions. Balance oversized pieces with fitted ones. This creates a flattering silhouette that works for any body type."

[SCENE 7: TIP 5 (36-43 seconds)
Visual: Final styled look
Text Overlay: "Tip #5: Confidence is Key"
Narration: "Fifth tip: Confidence is your best accessory. When you feel good in what you're wearing, it shows. Own your style choices!"

[SCENE 8: CALL TO ACTION (43-45 seconds)
Visual: Text overlay with social media handles
Text Overlay: "Follow for more style tips!"
Narration: "What's your go-to {self._get_fashion_category()} piece? Let me know in the comments and don't forget to follow for more fashion inspiration!""",
                "platform": f"{platform.title()} Reels/TikTok",
                "duration": "45 seconds",
                "hashtags": "#fashion #ootd #style #outfit #fashionista #trending #styleinspo #fashiontips #styling #fashionhacks"
            },
            {
                "script": "Fashion Haul & Try-On",
                "content": f"""VIDEO SCRIPT: "Shopping Haul: 5 Pieces That Will Change Your Wardrobe"

[SCENE 1: HOOK (0-3 seconds)
Visual: Exciting shopping bags and clothing items
Text Overlay: "Shopping Haul That Will Blow Your Mind"
Narration: "I just went shopping and found some incredible pieces that will transform your wardrobe!"

[SCENE 2: INTRODUCTION (3-8 seconds)
Visual: Person speaking to camera with shopping bags
Text Overlay: "Hi, I'm [Your Name]"
Narration: "Hi there! I'm [Your Name], and I'm so excited to show you what I found. These pieces are game-changers!"

[SCENE 3: PIECE 1 (8-18 seconds)
Visual: Showing the first item from different angles
Text Overlay: "Piece #1: {self._get_fashion_item().title()}"
Narration: "First up, this amazing {self._get_fashion_item()} from {self._get_fashion_brand()}. Look at how it fits - {self._get_fashion_fit_description()}. The quality is {self._get_fashion_quality_description()} and I love the {self._get_fashion_detail()}."

[SCENE 4: PIECE 2 (18-28 seconds)
Visual: Trying on the second item
Text Overlay: "Piece #2: {self._get_fashion_item().title()}"
Narration: "Next, this {self._get_fashion_item()} is perfect for {self._get_fashion_occasion()}. The {self._get_fashion_color()} color adds {self._get_fashion_style_tip()} to any outfit."

[SCENE 5: PIECE 3 (28-38 seconds)
Visual: Styling the third piece
Text Overlay: "Piece #3: {self._get_fashion_item().title()}"
Narration: "This {self._get_fashion_item()} is a {self._get_fashion_category()} piece that you'll wear on repeat. The {self._get_fashion_detail()} makes it special."

[SCENE 6: STYLING TIPS (38-45 seconds)
Visual: Showing how to style the pieces
Text Overlay: "Pro Styling Tips"
Narration: "The key to making these pieces work is {self._get_fashion_styling_tip()}. Mix and match for endless outfit possibilities!"

[SCENE 7: CALL TO ACTION (45-48 seconds)
Visual: Text overlay with social media handles
Text Overlay: "What should I keep?"
Narration: "What do you think? Should I keep all of them? Let me know in the comments and follow for more fashion hauls!""",
                "platform": f"{platform.title()} Reels/YouTube Shorts",
                "duration": "48 seconds",
                "hashtags": "#fashionhaul #tryon #shopping #fashion #haul #outfit #style #fashionista #haul #shopping #fashionhaul"
            },
            {
                "script": "Fashion Trend Breakdown",
                "content": f"""VIDEO SCRIPT: "Trend Alert: {self._get_fashion_trend().title()} - How to Style It Right"

[SCENE 1: HOOK (0-3 seconds)
Visual: Trending hashtags and fashion images
Text Overlay: "Trend Alert: {self._get_fashion_trend().title()}"
Narration: "This {self._get_fashion_trend()} trend is everywhere right now, and I have thoughts!"

[SCENE 2: INTRODUCTION (3-8 seconds)
Visual: Person speaking to camera with trend items
Text Overlay: "Hi, I'm [Your Name]"
Narration: "Hi there! I'm [Your Name], and today I'm breaking down the {self._get_fashion_trend()} trend and how to style it right."

[SCENE 3: TREND ANALYSIS (8-18 seconds)
Visual: Showing the trend in different contexts
Text Overlay: "Why This Trend Works"
Narration: "Here's why this trend is so popular: it's {self._get_fashion_trend_tip()}. But the key is to {self._get_fashion_trend_key()} so you don't look like everyone else."

[SCENE 4: STYLING TIPS (18-28 seconds)
Visual: Demonstrating different styling approaches
Text Overlay: "How to Style It"
Narration: "I'm pairing it with {self._get_fashion_trend_pairing()} to make it my own. This creates a unique look that's still on-trend."

[SCENE 5: DO'S AND DON'TS (28-38 seconds)
Visual: Split screen showing good vs bad examples
Text Overlay: "Do's and Don'ts"
Narration: "Do: {self._get_fashion_tip_1()}. Don't: {self._get_fashion_tip_2()}. The goal is to make the trend work for your personal style."

[SCENE 6: CALL TO ACTION (38-42 seconds)
Visual: Text overlay with social media handles
Text Overlay: "What's Your Take?"
Narration: "What's your take on this trend? Are you in or out? Let me know in the comments and follow for more trend breakdowns!""",
                "platform": f"{platform.title()} Stories/TikTok",
                "duration": "42 seconds",
                "hashtags": "#fashiontrend #trending #fashion #style #outfit #fashionista #trendalert #fashion #trending #style"
            },
            {
                "script": "Fashion Styling Tips",
                "content": f"""VIDEO SCRIPT: "3 Styling Hacks That Will Transform Your Outfits"

[SCENE 1: HOOK (0-3 seconds)
Visual: Before and after outfit transformations
Text Overlay: "3 Styling Hacks That Changed Everything"
Narration: "These three styling tips will change your fashion game forever!"

[SCENE 2: INTRODUCTION (3-8 seconds)
Visual: Person speaking to camera in stylish outfit
Text Overlay: "Hi, I'm [Your Name]"
Narration: "Hi there! I'm [Your Name], and today I'm sharing three styling hacks that will make any outfit look expensive and put-together."

[SCENE 3: HACK 1 (8-18 seconds)
Visual: Demonstrating the first styling tip
Text Overlay: "Hack #1: {self._get_fashion_tip_1().title()}"
Narration: "First hack: {self._get_fashion_tip_1()}. This simple trick instantly elevates your look and creates a more polished appearance."

[SCENE 4: HACK 2 (18-28 seconds)
Visual: Showing the second styling technique
Text Overlay: "Hack #2: {self._get_fashion_tip_2().title()}"
Narration: "Second hack: {self._get_fashion_tip_2()}. This technique adds visual interest and makes your outfit look more intentional and styled."

[SCENE 5: HACK 3 (28-38 seconds)
Visual: Demonstrating the third styling tip
Text Overlay: "Hack #3: {self._get_fashion_tip_3().title()}"
Narration: "Third hack: {self._get_fashion_tip_3()}. This final tip ties everything together and creates a cohesive, professional look."

[SCENE 6: BEFORE & AFTER (38-45 seconds)
Visual: Side-by-side comparison of styled vs unstyled looks
Text Overlay: "See the Difference?"
Narration: "See how these simple tricks transform the entire look? The difference is incredible!"

[SCENE 7: CALL TO ACTION (45-48 seconds)
Visual: Text overlay with social media handles
Text Overlay: "Try These Hacks!"
Narration: "Try these hacks and let me know how it goes! Follow for more styling tips and fashion inspiration!""",
                "platform": f"{platform.title()} Post/Reels",
                "duration": "48 seconds",
                "hashtags": "#fashiontips #styling #fashion #style #outfit #fashionista #tips #fashionhacks #styling #fashiontips"
            },
            {
                "script": "Fashion Behind-the-Scenes",
                "content": f"""VIDEO SCRIPT: "Behind the Scenes: {self._get_fashion_content_type().title()} Shoot"

[SCENE 1: HOOK (0-3 seconds)
Visual: Quick montage of behind-the-scenes moments
Text Overlay: "Behind the Scenes: {self._get_fashion_content_type().title()}"
Narration: "Ever wondered what goes into creating fashion content? Let me show you!"

[SCENE 2: INTRODUCTION (3-8 seconds)
Visual: Person speaking to camera in casual behind-the-scenes setting
Text Overlay: "Hi, I'm [Your Name]"
Narration: "Hi there! I'm [Your Name], and today I'm taking you behind the scenes of my {self._get_fashion_content_type()} shoot!"

[SCENE 3: PREPARATION (8-18 seconds)
Visual: Setting up equipment and styling area
Text Overlay: "Step 1: {self._get_fashion_bts_1().title()}"
Narration: "First, we start with {self._get_fashion_bts_1()}. This is where the magic begins - {self._get_fashion_bts_2()} to get everything just right."

[SCENE 4: THE PROCESS (18-28 seconds)
Visual: Actual shooting process and styling
Text Overlay: "Step 2: The Shoot"
Narration: "Then comes the actual shoot. This is what really goes into creating fashion content - it's not as glamorous as it looks!"

[SCENE 5: CHALLENGES (28-38 seconds)
Visual: Showing the difficult parts and retakes
Text Overlay: "The Reality"
Narration: "The hardest part is {self._get_fashion_bts_challenge()}. But when you get that perfect shot, it's all worth it!"

[SCENE 6: FINAL RESULT (38-45 seconds)
Visual: Showing the final edited content
Text Overlay: "The Result"
Narration: "And this is what we create - content that inspires and connects with our audience. The process is intense, but the result is always worth it!"

[SCENE 7: CALL TO ACTION (45-48 seconds)
Visual: Text overlay with social media handles
Text Overlay: "What would you like to see?"
Narration: "What would you like to see more of? Let me know in the comments and follow for more behind-the-scenes content!""",
                "platform": f"{platform.title()} Stories/YouTube Shorts",
                "duration": "48 seconds",
                "hashtags": "#behindthescenes #fashion #contentcreation #bts #fashionista #style #process #bts #fashion #contentcreation"
            }
        ]
    
    def _generate_lifestyle_content_scripts(self, platform: str, user_level: str) -> List[Dict[str, str]]:
        """Generate lifestyle-specific content scripts"""
        return [
            {
                "script": "Morning Routine",
                "content": f"Good morning! Here's how I start my day for maximum productivity and good vibes. First, I {self._get_morning_activity_1()}, then I {self._get_morning_activity_2()}. The key to my morning routine is {self._get_morning_tip()}. This sets me up for a {self._get_morning_benefit()} day. What's your morning routine? Share it below!",
                "platform": f"{platform.title()} Reels/TikTok",
                "duration": "30-45 seconds",
                "hashtags": "#morningroutine #lifestyle #productivity #wellness #selfcare #motivation #routine"
            },
            {
                "script": "Home Organization Tips",
                "content": f"Three organization tips that will transform your space: First, {self._get_organization_tip_1()}. Second, {self._get_organization_tip_2()}. And third, {self._get_organization_tip_3()}. These simple changes make such a difference in how your space feels. Try them and let me know how it goes!",
                "platform": f"{platform.title()} Post/Reels",
                "duration": "25-35 seconds",
                "hashtags": "#organization #home #lifestyle #tips #cleaning #organization #productivity"
            },
            {
                "script": "Lifestyle Day in My Life",
                "content": f"Come with me for a day in my life! Today I'm {self._get_daily_activity_1()}, then {self._get_daily_activity_2()}. I love how {self._get_daily_highlight()} makes me feel. The best part of my day is {self._get_daily_best_part()}. What's your favorite part of the day? Let me know!",
                "platform": f"{platform.title()} Reels/YouTube Shorts",
                "duration": "45-60 seconds",
                "hashtags": "#dayinmylife #lifestyle #vlog #daily #life #routine #lifestyle"
            },
            {
                "script": "Wellness & Self-Care",
                "content": f"Self-care isn't selfish, it's essential! Today I'm focusing on {self._get_wellness_activity()}. I love how {self._get_wellness_benefit()} makes me feel. My go-to self-care routine includes {self._get_wellness_routine()}. What's your favorite way to practice self-care?",
                "platform": f"{platform.title()} Stories/Post",
                "duration": "20-30 seconds",
                "hashtags": "#selfcare #wellness #lifestyle #mentalhealth #selflove #wellness #mindfulness"
            },
            {
                "script": "Lifestyle Tips & Tricks",
                "content": f"Quick lifestyle hack that will save you time and stress: {self._get_lifestyle_hack()}. I've been using this trick for {self._get_hack_duration()} and it's been a game-changer. The best part is {self._get_hack_benefit()}. Try it and let me know if it works for you!",
                "platform": f"{platform.title()} Reels/TikTok",
                "duration": "15-25 seconds",
                "hashtags": "#lifestylehack #tips #lifestyle #productivity #hack #lifehack #organization"
            }
        ]
    
    def _generate_fitness_content_scripts(self, platform: str, user_level: str) -> List[Dict[str, str]]:
        """Generate fitness-specific content scripts"""
        return [
            {
                "script": "Workout Motivation",
                "content": f"Let's get moving! Today's workout is all about {self._get_workout_focus()}. I love how {self._get_workout_benefit()} makes me feel. Remember, {self._get_fitness_motivation()}. Every rep counts, every step matters. What's your favorite way to stay active?",
                "platform": f"{platform.title()} Reels/TikTok",
                "duration": "25-35 seconds",
                "hashtags": "#fitness #workout #motivation #fitnessmotivation #exercise #health #wellness"
            },
            {
                "script": "Fitness Tutorial",
                "content": f"Today I'm teaching you the proper form for {self._get_exercise_name()}. Here's how to do it: {self._get_exercise_instruction()}. The key points are {self._get_exercise_key_points()}. This exercise targets {self._get_exercise_target()}. Try it and let me know how it feels!",
                "platform": f"{platform.title()} Reels/YouTube Shorts",
                "duration": "30-45 seconds",
                "hashtags": "#fitness #exercise #tutorial #workout #form #exercise #fitness"
            },
            {
                "script": "Fitness Journey Update",
                "content": f"Fitness journey update! I've been {self._get_fitness_activity()} for {self._get_fitness_duration()} and I'm feeling {self._get_fitness_feeling()}. The biggest change I've noticed is {self._get_fitness_change()}. My goal is {self._get_fitness_goal()}. What's your fitness goal? Let's support each other!",
                "platform": f"{platform.title()} Post/Stories",
                "duration": "20-30 seconds",
                "hashtags": "#fitnessjourney #progress #fitness #health #wellness #motivation #fitness"
            },
            {
                "script": "Healthy Recipe",
                "content": f"Quick and healthy recipe that's perfect for {self._get_meal_occasion()}: {self._get_recipe_name()}. You'll need {self._get_recipe_ingredients()}. Here's how to make it: {self._get_recipe_instructions()}. It's {self._get_recipe_benefit()} and so delicious! Try it and let me know what you think!",
                "platform": f"{platform.title()} Reels/YouTube Shorts",
                "duration": "45-60 seconds",
                "hashtags": "#healthyrecipe #fitness #nutrition #health #cooking #recipe #healthy"
            },
            {
                "script": "Fitness Tips",
                "content": f"Three fitness tips that will help you reach your goals: First, {self._get_fitness_tip_1()}. Second, {self._get_fitness_tip_2()}. And third, {self._get_fitness_tip_3()}. These simple changes make a huge difference. What's your favorite fitness tip?",
                "platform": f"{platform.title()} Post/Reels",
                "duration": "25-35 seconds",
                "hashtags": "#fitness #tips #health #wellness #fitness #exercise #motivation"
            }
        ]
    
    def _generate_general_content_scripts(self, platform: str, user_level: str) -> List[Dict[str, str]]:
        """Generate general content scripts"""
        return [
            {
                "script": "Day in My Life",
                "content": f"Come with me for a day in my life! Today I'm {self._get_general_activity_1()}, then {self._get_general_activity_2()}. I love how {self._get_general_highlight()} makes me feel. The best part of my day is {self._get_general_best_part()}. What's your favorite part of the day?",
                "platform": f"{platform.title()} Reels/YouTube Shorts",
                "duration": "45-60 seconds",
                "hashtags": "#dayinmylife #lifestyle #vlog #daily #life #routine #lifestyle"
            },
            {
                "script": "Quick Tips",
                "content": f"Quick tip that will help you {self._get_general_benefit()}: {self._get_general_tip()}. I've been using this for {self._get_general_duration()} and it's been amazing. The best part is {self._get_general_tip_benefit()}. Try it and let me know how it works!",
                "platform": f"{platform.title()} Reels/TikTok",
                "duration": "20-30 seconds",
                "hashtags": "#tips #lifestyle #hack #productivity #lifehack #tips #motivation"
            },
            {
                "script": "Behind the Scenes",
                "content": f"Behind the scenes of {self._get_general_content_type()}! This is what really goes into {self._get_general_process()}. From {self._get_general_bts_1()} to {self._get_general_bts_2()}, it's a whole process! The hardest part is {self._get_general_challenge()}, but the result is always worth it.",
                "platform": f"{platform.title()} Stories/YouTube Shorts",
                "duration": "30-45 seconds",
                "hashtags": "#behindthescenes #bts #contentcreation #process #real #lifestyle"
            },
            {
                "script": "Community Question",
                "content": f"Quick question for my amazing community: {self._get_general_question()}? I'm really curious about your experiences with this. Drop your answers in the comments and let's start a conversation! Don't forget to follow for more discussions!",
                "platform": f"{platform.title()} Post/Story",
                "duration": "20-30 seconds",
                "hashtags": "#community #question #discussion #engagement #conversation #lifestyle"
            },
            {
                "script": "Motivational Message",
                "content": f"Remember, {self._get_general_motivation()}. Every day is a new opportunity to {self._get_general_opportunity()}. I believe in you and your ability to {self._get_general_belief()}. What's one thing you're grateful for today? Let me know!",
                "platform": f"{platform.title()} Post/Stories",
                "duration": "15-25 seconds",
                "hashtags": "#motivation #inspiration #positive #mindset #gratitude #lifestyle #motivation"
            }
        ]
    
    # Helper methods for generating dynamic content
    def _get_fashion_item(self) -> str:
        return random.choice(["blazer", "dress", "jeans", "sweater", "jacket", "top", "skirt", "pants"])
    
    def _get_fashion_accessory(self) -> str:
        return random.choice(["statement necklace", "belt", "scarf", "bag", "shoes", "earrings", "watch"])
    
    def _get_fashion_color(self) -> str:
        return random.choice(["navy", "black", "white", "beige", "camel", "burgundy", "olive", "gray"])
    
    def _get_fashion_style_tip(self) -> str:
        return random.choice(["sophistication", "edge", "elegance", "casual chic", "professional polish"])
    
    def _get_fashion_styling_tip(self) -> str:
        return random.choice(["to balance proportions", "to add texture", "to create contrast", "to define the waist", "to add interest"])
    
    def _get_fashion_category(self) -> str:
        return random.choice(["statement", "basic", "trendy", "classic", "vintage", "modern"])
    
    def _get_fashion_brand(self) -> str:
        return random.choice(["Zara", "H&M", "Mango", "COS", "Arket", "Massimo Dutti", "Uniqlo"])
    
    def _get_fashion_fit_description(self) -> str:
        return random.choice(["perfect", "flattering", "comfortable", "tailored", "relaxed"])
    
    def _get_fashion_quality_description(self) -> str:
        return random.choice(["amazing", "incredible", "surprising", "excellent", "outstanding"])
    
    def _get_fashion_detail(self) -> str:
        return random.choice(["buttons", "stitching", "fabric", "cut", "finish", "hardware"])
    
    def _get_fashion_occasion(self) -> str:
        return random.choice(["work", "date night", "weekend", "travel", "special event", "everyday"])
    
    def _get_fashion_trend(self) -> str:
        return random.choice(["oversized blazers", "cargo pants", "platform shoes", "micro bags", "layered jewelry"])
    
    def _get_fashion_trend_tip(self) -> str:
        return random.choice(["to add your own twist", "to make it your own", "to personalize it", "to stand out"])
    
    def _get_fashion_trend_key(self) -> str:
        return random.choice(["to balance it", "to accessorize wisely", "to keep it simple", "to add contrast"])
    
    def _get_fashion_trend_pairing(self) -> str:
        return random.choice(["classic pieces", "neutral colors", "minimal accessories", "simple basics"])
    
    def _get_fashion_tip_1(self) -> str:
        return random.choice(["always define your waist", "mix textures for interest", "invest in good basics", "accessorize strategically"])
    
    def _get_fashion_tip_2(self) -> str:
        return random.choice(["play with proportions", "layer strategically", "choose quality over quantity", "experiment with color"])
    
    def _get_fashion_tip_3(self) -> str:
        return random.choice(["tailor your pieces", "mix high and low", "find your signature style", "dress for your body type"])
    
    def _get_fashion_content_type(self) -> str:
        return random.choice(["outfit shoot", "styling session", "haul video", "try-on", "lookbook"])
    
    def _get_fashion_bts_1(self) -> str:
        return random.choice(["styling the looks", "setting up the shot", "choosing the location", "planning the outfits"])
    
    def _get_fashion_bts_2(self) -> str:
        return random.choice(["getting the right angles", "coordinating accessories", "adjusting lighting", "capturing the details"])
    
    def _get_fashion_bts_challenge(self) -> str:
        return random.choice(["getting the perfect shot", "coordinating everything", "timing the lighting", "capturing the essence"])
    
    def _get_morning_activity_1(self) -> str:
        return random.choice(["drink a glass of water", "stretch for 5 minutes", "write in my journal", "meditate for 10 minutes"])
    
    def _get_morning_activity_2(self) -> str:
        return random.choice(["make my bed", "prepare a healthy breakfast", "review my goals", "check my schedule"])
    
    def _get_morning_tip(self) -> str:
        return random.choice(["consistency", "starting slow", "listening to my body", "setting intentions"])
    
    def _get_morning_benefit(self) -> str:
        return random.choice(["productive", "peaceful", "energized", "focused", "balanced"])
    
    def _get_organization_tip_1(self) -> str:
        return random.choice(["everything has a place", "declutter regularly", "use storage solutions", "label everything"])
    
    def _get_organization_tip_2(self) -> str:
        return random.choice(["one in, one out rule", "group similar items", "create systems", "maintain daily"])
    
    def _get_organization_tip_3(self) -> str:
        return random.choice(["start small", "be consistent", "make it beautiful", "keep it simple"])
    
    def _get_daily_activity_1(self) -> str:
        return random.choice(["working on my projects", "running errands", "meeting friends", "exploring the city"])
    
    def _get_daily_activity_2(self) -> str:
        return random.choice(["cooking a new recipe", "reading a book", "working out", "creating content"])
    
    def _get_daily_highlight(self) -> str:
        return random.choice(["this moment", "this experience", "this connection", "this learning"])
    
    def _get_daily_best_part(self) -> str:
        return random.choice(["connecting with others", "learning something new", "creating something", "helping someone"])
    
    def _get_wellness_activity(self) -> str:
        return random.choice(["meditation", "yoga", "journaling", "nature walks", "breathing exercises"])
    
    def _get_wellness_benefit(self) -> str:
        return random.choice(["centered", "calm", "focused", "peaceful", "balanced"])
    
    def _get_wellness_routine(self) -> str:
        return random.choice(["morning meditation", "evening journaling", "weekly nature time", "daily gratitude practice"])
    
    def _get_lifestyle_hack(self) -> str:
        return random.choice(["prep meals on Sunday", "lay out clothes the night before", "use a timer for tasks", "create morning and evening routines"])
    
    def _get_hack_duration(self) -> str:
        return random.choice(["months", "weeks", "years", "a while"])
    
    def _get_hack_benefit(self) -> str:
        return random.choice(["saves so much time", "reduces stress", "makes life easier", "creates more space"])
    
    def _get_workout_focus(self) -> str:
        return random.choice(["strength training", "cardio", "flexibility", "balance", "endurance"])
    
    def _get_workout_benefit(self) -> str:
        return random.choice(["strong", "energized", "confident", "accomplished", "powerful"])
    
    def _get_fitness_motivation(self) -> str:
        return random.choice(["progress over perfection", "consistency is key", "every step counts", "you're stronger than you think"])
    
    def _get_exercise_name(self) -> str:
        return random.choice(["squats", "push-ups", "planks", "lunges", "burpees", "mountain climbers"])
    
    def _get_exercise_instruction(self) -> str:
        return random.choice(["start in position", "engage your core", "maintain proper form", "breathe steadily"])
    
    def _get_exercise_key_points(self) -> str:
        return random.choice(["keep your back straight", "engage your core", "breathe properly", "maintain alignment"])
    
    def _get_exercise_target(self) -> str:
        return random.choice(["your core", "your legs", "your arms", "your glutes", "your entire body"])
    
    def _get_fitness_activity(self) -> str:
        return random.choice(["working out", "running", "yoga", "strength training", "dancing"])
    
    def _get_fitness_duration(self) -> str:
        return random.choice(["weeks", "months", "a year", "a while"])
    
    def _get_fitness_feeling(self) -> str:
        return random.choice(["stronger", "more confident", "energized", "accomplished", "proud"])
    
    def _get_fitness_change(self) -> str:
        return random.choice(["my energy levels", "my strength", "my confidence", "my overall health", "my mood"])
    
    def _get_fitness_goal(self) -> str:
        return random.choice(["to get stronger", "to feel healthier", "to build confidence", "to improve my fitness", "to maintain consistency"])
    
    def _get_meal_occasion(self) -> str:
        return random.choice(["post-workout", "breakfast", "lunch", "dinner", "snack time"])
    
    def _get_recipe_name(self) -> str:
        return random.choice(["protein smoothie", "quinoa bowl", "grilled chicken salad", "overnight oats", "energy balls"])
    
    def _get_recipe_ingredients(self) -> str:
        return random.choice(["protein powder, banana, and almond milk", "quinoa, vegetables, and tahini", "chicken, greens, and avocado", "oats, chia seeds, and berries"])
    
    def _get_recipe_instructions(self) -> str:
        return random.choice(["blend everything together", "cook and combine", "mix and refrigerate", "bake for 20 minutes"])
    
    def _get_recipe_benefit(self) -> str:
        return random.choice(["nutritious", "delicious", "easy to make", "perfect for meal prep"])
    
    def _get_fitness_tip_1(self) -> str:
        return random.choice(["consistency over intensity", "listen to your body", "start where you are", "progress takes time"])
    
    def _get_fitness_tip_2(self) -> str:
        return random.choice(["form is everything", "rest is part of training", "nutrition matters", "small steps add up"])
    
    def _get_fitness_tip_3(self) -> str:
        return random.choice(["find what you enjoy", "set realistic goals", "celebrate progress", "be patient with yourself"])
    
    def _get_general_activity_1(self) -> str:
        return random.choice(["working on my projects", "exploring new places", "learning something new", "connecting with friends"])
    
    def _get_general_activity_2(self) -> str:
        return random.choice(["creating content", "pursuing my passions", "helping others", "building my dreams"])
    
    def _get_general_highlight(self) -> str:
        return random.choice(["this experience", "this moment", "this connection", "this learning"])
    
    def _get_general_best_part(self) -> str:
        return random.choice(["connecting with you", "sharing my journey", "learning and growing", "making a difference"])
    
    def _get_general_benefit(self) -> str:
        return random.choice(["be more productive", "feel more organized", "reduce stress", "achieve your goals"])
    
    def _get_general_tip(self) -> str:
        return random.choice(["start with small steps", "focus on one thing at a time", "be consistent", "celebrate progress"])
    
    def _get_general_duration(self) -> str:
        return random.choice(["weeks", "months", "a while", "some time"])
    
    def _get_general_tip_benefit(self) -> str:
        return random.choice(["it's so simple", "it works every time", "it's life-changing", "it's effective"])
    
    def _get_general_content_type(self) -> str:
        return random.choice(["content creation", "project work", "creative process", "daily routine"])
    
    def _get_general_process(self) -> str:
        return random.choice(["creating content", "working on projects", "building something", "pursuing goals"])
    
    def _get_general_bts_1(self) -> str:
        return random.choice(["planning and preparation", "research and development", "creative brainstorming", "initial setup"])
    
    def _get_general_bts_2(self) -> str:
        return random.choice(["execution and creation", "refinement and editing", "final touches", "quality control"])
    
    def _get_general_challenge(self) -> str:
        return random.choice(["getting everything just right", "balancing quality and speed", "staying focused", "managing time"])
    
    def _get_general_question(self) -> str:
        return random.choice(["What's your biggest challenge right now", "What motivates you most", "What's your favorite way to learn", "What's one thing you want to improve"])
    
    def _get_general_motivation(self) -> str:
        return random.choice(["you're capable of amazing things", "every day is a new opportunity", "progress is progress", "you're exactly where you need to be"])
    
    def _get_general_opportunity(self) -> str:
        return random.choice(["grow and improve", "learn something new", "make a difference", "create something amazing"])
    
    def _get_general_belief(self) -> str:
        return random.choice(["achieve your goals", "overcome any challenge", "create the life you want", "make your dreams reality"])
