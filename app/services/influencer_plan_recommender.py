from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

class InfluencerPlanRecommender:
    def __init__(self):
        self.plan_templates = {
            "beginner": {
                "posting_frequency": "3-4 posts per week",
                "content_types": ["lifestyle", "behind-the-scenes", "product_reviews"],
                "engagement_goals": "5% engagement rate",
                "follower_growth": "10% monthly growth",
                "pricing_strategy": "competitive rates"
            },
            "intermediate": {
                "posting_frequency": "5-6 posts per week",
                "content_types": ["educational", "entertainment", "collaborations"],
                "engagement_goals": "7% engagement rate",
                "follower_growth": "15% monthly growth",
                "pricing_strategy": "premium rates"
            },
            "advanced": {
                "posting_frequency": "daily posts",
                "content_types": ["exclusive_content", "live_streams", "mentorship"],
                "engagement_goals": "10% engagement rate",
                "follower_growth": "20% monthly growth",
                "pricing_strategy": "luxury rates"
            }
        }
        
    async def generate_monthly_plans(self, user_profile: Dict[str, Any], 
                                   ai_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive monthly influencer plans"""
        
        # Determine user level
        user_level = await self._determine_user_level(user_profile, ai_recommendations)
        
        # Generate base plan
        base_plan = await self._generate_base_plan(user_level, user_profile)
        
        # Enhance with AI recommendations
        enhanced_plan = await self._enhance_with_ai_recommendations(
            base_plan=base_plan,
            ai_recommendations=ai_recommendations,
            user_profile=user_profile
        )
        
        # Create detailed monthly schedule
        monthly_schedule = await self._create_monthly_schedule(enhanced_plan)
        
        # Generate performance goals
        performance_goals = await self._generate_performance_goals(
            user_profile=user_profile,
            user_level=user_level
        )
        
        # Create pricing recommendations
        pricing_recommendations = await self._generate_pricing_recommendations(
            user_profile=user_profile,
            user_level=user_level
        )
        
        return {
            "user_id": user_profile["user"].id,
            "user_level": user_level,
            "base_plan": base_plan,
            "enhanced_plan": enhanced_plan,
            "monthly_schedule": monthly_schedule,
            "performance_goals": performance_goals,
            "pricing_recommendations": pricing_recommendations,
            "ai_insights": ai_recommendations.get("agent_responses", []),
            "generated_at": datetime.now(),
            "valid_until": datetime.now() + timedelta(days=30)
        }
        
    async def _determine_user_level(self, user_profile: Dict[str, Any], 
                                  ai_recommendations: Dict[str, Any]) -> str:
        """Determine user level based on profile and AI analysis"""
        
        engagement_rate = user_profile.get("performance_metrics", {}).get("engagement_rate", 0)
        follower_count = user_profile.get("influencer", {}).get("follower_count", 0)
        revenue = user_profile.get("financial_analysis", {}).get("total_revenue", 0)
        
        # Advanced level criteria
        if (engagement_rate >= 8.0 and follower_count >= 10000 and revenue >= 5000):
            return "advanced"
            
        # Intermediate level criteria
        elif (engagement_rate >= 5.0 and follower_count >= 5000 and revenue >= 2000):
            return "intermediate"
            
        # Beginner level (default)
        else:
            return "beginner"
            
    async def _generate_base_plan(self, user_level: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate base plan based on user level"""
        
        base_template = self.plan_templates[user_level]
        
        return {
            "level": user_level,
            "posting_frequency": base_template["posting_frequency"],
            "content_types": base_template["content_types"],
            "engagement_goals": base_template["engagement_goals"],
            "follower_growth": base_template["follower_growth"],
            "pricing_strategy": base_template["pricing_strategy"],
            "estimated_hours_per_week": self._get_hours_per_week(user_level),
            "content_creation_tips": self._get_content_tips(user_level),
            "platform_recommendations": self._get_platform_recommendations(user_profile)
        }
        
    async def _enhance_with_ai_recommendations(self, base_plan: Dict[str, Any], 
                                             ai_recommendations: Dict[str, Any], 
                                             user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance base plan with AI agent recommendations"""
        
        enhanced_plan = base_plan.copy()
        
        # Extract insights from AI responses
        ai_insights = []
        for response in ai_recommendations.get("agent_responses", []):
            if response.get("status") == "success":
                ai_insights.append({
                    "agent_type": response.get("agent_type"),
                    "focus_area": response.get("focus_area"),
                    "insights": response.get("response")
                })
                
        enhanced_plan["ai_enhancements"] = ai_insights
        
        # Customize based on improvement areas
        improvement_areas = user_profile.get("improvement_areas", [])
        
        if "engagement_rate" in improvement_areas:
            enhanced_plan["engagement_strategies"] = [
                "Interactive polls and questions",
                "Behind-the-scenes content",
                "User-generated content campaigns",
                "Live Q&A sessions"
            ]
            
        if "content_consistency" in improvement_areas:
            enhanced_plan["consistency_tools"] = [
                "Content calendar template",
                "Automated posting reminders",
                "Batch content creation",
                "Theme-based content series"
            ]
            
        if "pricing_strategy" in improvement_areas:
            enhanced_plan["pricing_optimization"] = [
                "Market rate analysis",
                "Value-based pricing",
                "Package deals",
                "Premium service tiers"
            ]
            
        return enhanced_plan
        
    async def _create_monthly_schedule(self, enhanced_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed monthly posting schedule"""
        
        # Calculate posts per week
        frequency = enhanced_plan["posting_frequency"]
        if "3-4" in frequency:
            posts_per_week = 3.5
        elif "5-6" in frequency:
            posts_per_week = 5.5
        else:
            posts_per_week = 7
            
        # Create 4-week schedule
        schedule = {
            "week_1": {
                "monday": {"content_type": "lifestyle", "theme": "motivation"},
                "wednesday": {"content_type": "educational", "theme": "tips_and_tricks"},
                "friday": {"content_type": "behind-the-scenes", "theme": "daily_routine"},
                "sunday": {"content_type": "engagement", "theme": "q&a"}
            },
            "week_2": {
                "tuesday": {"content_type": "product_review", "theme": "recommendations"},
                "thursday": {"content_type": "entertainment", "theme": "fun_content"},
                "saturday": {"content_type": "collaboration", "theme": "partner_content"}
            },
            "week_3": {
                "monday": {"content_type": "educational", "theme": "industry_insights"},
                "wednesday": {"content_type": "lifestyle", "theme": "personal_story"},
                "friday": {"content_type": "engagement", "theme": "poll_or_question"},
                "sunday": {"content_type": "behind-the-scenes", "theme": "work_process"}
            },
            "week_4": {
                "tuesday": {"content_type": "product_review", "theme": "new_products"},
                "thursday": {"content_type": "entertainment", "theme": "trending_topics"},
                "saturday": {"content_type": "collaboration", "theme": "cross_promotion"}
            }
        }
        
        return {
            "posts_per_week": posts_per_week,
            "total_posts_month": int(posts_per_week * 4),
            "schedule": schedule,
            "content_themes": self._get_content_themes(),
            "hashtag_strategies": self._get_hashtag_strategies()
        }
        
    async def _generate_performance_goals(self, user_profile: Dict[str, Any], 
                                        user_level: str) -> Dict[str, Any]:
        """Generate realistic performance goals"""
        
        current_engagement = user_profile.get("performance_metrics", {}).get("engagement_rate", 0)
        current_followers = user_profile.get("influencer", {}).get("follower_count", 0)
        current_revenue = user_profile.get("financial_analysis", {}).get("total_revenue", 0)
        
        # Calculate realistic goals based on current performance
        engagement_goal = min(current_engagement * 1.2, 15.0)  # Max 15%
        follower_goal = int(current_followers * 1.15)  # 15% growth
        revenue_goal = current_revenue * 1.25  # 25% growth
        
        return {
            "monthly_goals": {
                "engagement_rate": f"{engagement_goal:.1f}%",
                "follower_growth": f"{follower_goal:,} followers",
                "revenue_increase": f"${revenue_goal:,.0f}",
                "content_consistency": "90% posting consistency",
                "brand_collaborations": "2-3 new partnerships"
            },
            "quarterly_goals": {
                "engagement_rate": f"{min(engagement_goal * 1.1, 20.0):.1f}%",
                "follower_growth": f"{int(follower_goal * 1.1):,} followers",
                "revenue_increase": f"${revenue_goal * 1.5:,.0f}",
                "platform_expansion": "Add 1 new platform",
                "audience_quality": "Increase authentic engagement by 30%"
            },
            "success_metrics": [
                "Engagement rate improvement",
                "Follower quality (not just quantity)",
                "Brand partnership inquiries",
                "Content performance consistency",
                "Audience feedback and comments"
            ]
        }
        
    async def _generate_pricing_recommendations(self, user_profile: Dict[str, Any], 
                                              user_level: str) -> Dict[str, Any]:
        """Generate pricing strategy recommendations"""
        
        current_avg_rate = user_profile.get("financial_analysis", {}).get("average_rate", 0)
        
        # Calculate recommended rates based on level and current performance
        if user_level == "beginner":
            rate_multiplier = 1.2
        elif user_level == "intermediate":
            rate_multiplier = 1.5
        else:  # advanced
            rate_multiplier = 2.0
            
        recommended_rate = current_avg_rate * rate_multiplier if current_avg_rate > 0 else 100
        
        return {
            "current_average_rate": f"${current_avg_rate:,.0f}",
            "recommended_rate": f"${recommended_rate:,.0f}",
            "rate_increase": f"{((rate_multiplier - 1) * 100):.0f}%",
            "pricing_tiers": {
                "basic_package": f"${recommended_rate * 0.7:,.0f}",
                "standard_package": f"${recommended_rate:,.0f}",
                "premium_package": f"${recommended_rate * 1.5:,.0f}",
                "custom_package": "Negotiable"
            },
            "pricing_strategies": [
                "Value-based pricing based on audience size and engagement",
                "Package deals for multiple posts",
                "Premium rates for exclusive content",
                "Performance-based bonuses",
                "Long-term partnership discounts"
            ],
            "negotiation_tips": [
                "Highlight your unique value proposition",
                "Provide detailed analytics and case studies",
                "Offer multiple service tiers",
                "Consider long-term partnership benefits",
                "Be confident in your worth"
            ]
        }
        
    def _get_hours_per_week(self, user_level: str) -> int:
        """Get estimated hours per week based on user level"""
        return {"beginner": 10, "intermediate": 20, "advanced": 30}[user_level]
        
    def _get_content_tips(self, user_level: str) -> List[str]:
        """Get content creation tips based on user level"""
        tips = {
            "beginner": [
                "Focus on authentic, personal content",
                "Use trending hashtags strategically",
                "Engage with your audience regularly",
                "Post consistently, even if simple"
            ],
            "intermediate": [
                "Develop a unique content style",
                "Create educational and valuable content",
                "Collaborate with other creators",
                "Use analytics to optimize performance"
            ],
            "advanced": [
                "Create exclusive, premium content",
                "Develop multiple revenue streams",
                "Mentor other creators",
                "Build a personal brand empire"
            ]
        }
        return tips.get(user_level, [])
        
    def _get_platform_recommendations(self, user_profile: Dict[str, Any]) -> List[str]:
        """Get platform recommendations based on user profile"""
        audience = user_profile.get("audience_insights", {}).get("primary_audience", "general")
        
        platform_map = {
            "fashion": ["Instagram", "TikTok", "Pinterest"],
            "tech": ["LinkedIn", "Twitter", "YouTube"],
            "lifestyle": ["Instagram", "TikTok", "YouTube"],
            "business": ["LinkedIn", "Twitter", "Instagram"],
            "general": ["Instagram", "TikTok", "YouTube", "Twitter"]
        }
        
        return platform_map.get(audience, ["Instagram", "TikTok", "YouTube"])
        
    def _get_content_themes(self) -> List[str]:
        """Get content theme suggestions"""
        return [
            "Motivation Monday",
            "Tips Tuesday", 
            "Behind-the-Scenes Wednesday",
            "Throwback Thursday",
            "Feature Friday",
            "Weekend Vibes",
            "Sunday Reflection"
        ]
        
    def _get_hashtag_strategies(self) -> Dict[str, List[str]]:
        """Get hashtag strategy recommendations"""
        return {
            "branded_hashtags": ["#YourBrand", "#YourName", "#YourSignature"],
            "trending_hashtags": ["#Trending", "#Viral", "#Popular"],
            "niche_hashtags": ["#YourNiche", "#IndustrySpecific", "#TargetAudience"],
            "engagement_hashtags": ["#FollowMe", "#Like4Like", "#CommentBelow"]
        }
