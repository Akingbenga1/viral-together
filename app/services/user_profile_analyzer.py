from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

class UserProfileAnalyzer:
    def __init__(self):
        self.analysis_weights = {
            "engagement_rate": 0.3,
            "follower_growth": 0.2,
            "content_consistency": 0.15,
            "audience_demographics": 0.15,
            "revenue_performance": 0.2
        }
        
    def analyze_user_profile(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze comprehensive user profile"""
        
        analysis = {
            "user_id": user_profile["user"].id,
            "analysis_timestamp": datetime.now(),
            "profile_strengths": [],
            "profile_weaknesses": [],
            "improvement_areas": [],
            "performance_metrics": {},
            "audience_insights": {},
            "content_analysis": {},
            "financial_analysis": {},
            "recommendation_priorities": []
        }
        
        # Analyze influencer metrics
        if user_profile["influencer"]:
            analysis["performance_metrics"] = self._analyze_performance_metrics(
                user_profile["metrics"]
            )
            
        # Analyze rate cards and pricing
        if user_profile["rate_cards"]:
            analysis["financial_analysis"] = self._analyze_financial_performance(
                user_profile["rate_cards"],
                user_profile["metrics"]
            )
            
        # Analyze audience demographics
        analysis["audience_insights"] = self._analyze_audience_demographics(
            user_profile["influencer"]
        )
        
        # Analyze content consistency
        analysis["content_analysis"] = self._analyze_content_consistency(
            user_profile["metrics"]
        )
        
        # Generate improvement recommendations
        analysis["improvement_areas"] = self._identify_improvement_areas(analysis)
        
        # Set recommendation priorities
        analysis["recommendation_priorities"] = self._set_recommendation_priorities(analysis)
        
        return analysis
        
    def _analyze_performance_metrics(self, metrics: List) -> Dict[str, Any]:
        """Analyze performance metrics"""
        if not metrics:
            return {"engagement_rate": 0, "follower_growth": 0, "reach": 0}
            
        total_engagement = sum(m.engagement_rate for m in metrics if m.engagement_rate)
        total_followers = sum(m.follower_count for m in metrics if m.follower_count)
        total_reach = sum(m.reach_count for m in metrics if m.reach_count)
        
        return {
            "engagement_rate": total_engagement / len(metrics) if metrics else 0,
            "follower_growth": total_followers / len(metrics) if metrics else 0,
            "reach": total_reach / len(metrics) if metrics else 0,
            "metrics_count": len(metrics)
        }
        
    def _analyze_financial_performance(self, rate_cards: List, metrics: List) -> Dict[str, Any]:
        """Analyze financial performance"""
        total_revenue = sum(rc.price for rc in rate_cards if rc.price)
        avg_rate = total_revenue / len(rate_cards) if rate_cards else 0
        
        return {
            "total_revenue": total_revenue,
            "average_rate": avg_rate,
            "rate_cards_count": len(rate_cards),
            "revenue_trend": "increasing" if len(rate_cards) > 1 else "stable"
        }
        
    def _analyze_audience_demographics(self, influencer) -> Dict[str, Any]:
        """Analyze audience demographics"""
        if not influencer:
            return {}
            
        return {
            "location": influencer.location or "Unknown",
            "languages": influencer.languages or "English",
            "base_country_id": influencer.base_country_id,
            "availability": influencer.availability,
            "total_posts": influencer.total_posts or 0,
            "growth_rate": influencer.growth_rate or 0,
            "successful_campaigns": influencer.successful_campaigns or 0
        }
        
    def _analyze_content_consistency(self, metrics: List) -> Dict[str, Any]:
        """Analyze content consistency"""
        if not metrics:
            return {"consistency_score": 0, "posting_frequency": 0}
            
        # Calculate posting frequency
        recent_metrics = [m for m in metrics if m.created_at > datetime.now() - timedelta(days=30)]
        posting_frequency = len(recent_metrics) / 30 if recent_metrics else 0
        
        return {
            "consistency_score": min(posting_frequency * 10, 100),  # Scale to 100
            "posting_frequency": posting_frequency,
            "recent_posts": len(recent_metrics)
        }
        
    def _identify_improvement_areas(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement"""
        improvement_areas = []
        
        if analysis["performance_metrics"].get("engagement_rate", 0) < 3.0:
            improvement_areas.append("engagement_rate")
            
        if analysis["content_analysis"].get("consistency_score", 0) < 70:
            improvement_areas.append("content_consistency")
            
        if analysis["financial_analysis"].get("average_rate", 0) < 100:
            improvement_areas.append("pricing_strategy")
            
        return improvement_areas
        
    def _set_recommendation_priorities(self, analysis: Dict[str, Any]) -> List[str]:
        """Set recommendation priorities based on analysis"""
        priorities = []
        
        # High priority for engagement issues
        if "engagement_rate" in analysis["improvement_areas"]:
            priorities.append("content_optimization")
            priorities.append("audience_engagement")
            
        # Medium priority for consistency
        if "content_consistency" in analysis["improvement_areas"]:
            priorities.append("posting_schedule")
            priorities.append("content_calendar")
            
        # Lower priority for pricing
        if "pricing_strategy" in analysis["improvement_areas"]:
            priorities.append("rate_optimization")
            
        return priorities
