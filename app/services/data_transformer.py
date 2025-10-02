"""
Data transformation utilities for API responses.
This module provides functions to transform data structures to match UI expectations.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def transform_base_plan_for_ui(base_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform base_plan data structure to match UI expectations.
    
    Original structure:
    {
        "focus_areas": [...],
        "priority_level": "high",
        "recommendations": [
            {
                "agent_id": 1,
                "agent_type": "growth_advisor",
                "focus_area": "audience_growth",
                "response": "...",
                "status": "success",
                "context_used": {...}
            }
        ]
    }
    
    Transformed structure:
    [
        {
            "agent_id": 1,
            "agent_type": "growth_advisor",
            "focus_area": "audience_growth",
            "response": "...",
            "status": "success",
            "context_used": {...}
        }
    ]
    
    Args:
        base_plan: The original base_plan data structure
        
    Returns:
        Transformed base_plan as a flat array of recommendations
    """
    try:
        if not base_plan:
            logger.warning("Base plan is empty or None")
            return []
            
        # Check if base_plan already has the expected structure (array)
        if isinstance(base_plan, list):
            logger.info("Base plan is already in array format")
            return base_plan
            
        # Check if base_plan has the nested structure
        if isinstance(base_plan, dict) and "recommendations" in base_plan:
            recommendations = base_plan.get("recommendations", [])
            logger.info(f"Transforming base_plan: extracted {len(recommendations)} recommendations")
            return recommendations
            
        # If base_plan is a dict but doesn't have recommendations, return as is
        logger.warning("Base plan doesn't have expected structure, returning as is")
        return base_plan
        
    except Exception as e:
        logger.error(f"Error transforming base_plan: {str(e)}")
        # Return original data if transformation fails
        return base_plan

def transform_enhanced_plan_for_ui(enhanced_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform enhanced_plan data structure to match UI expectations.
    
    Args:
        enhanced_plan: The original enhanced_plan data structure
        
    Returns:
        Transformed enhanced_plan
    """
    try:
        if not enhanced_plan:
            logger.warning("Enhanced plan is empty or None")
            return {}
            
        # Check if enhanced_plan already has the expected structure
        if isinstance(enhanced_plan, list):
            logger.info("Enhanced plan is already in array format")
            return enhanced_plan
            
        # Check if enhanced_plan has the nested structure
        if isinstance(enhanced_plan, dict) and "recommendations" in enhanced_plan:
            recommendations = enhanced_plan.get("recommendations", [])
            logger.info(f"Transforming enhanced_plan: extracted {len(recommendations)} recommendations")
            return recommendations
            
        # If enhanced_plan is a dict but doesn't have recommendations, return as is
        logger.warning("Enhanced plan doesn't have expected structure, returning as is")
        return enhanced_plan
        
    except Exception as e:
        logger.error(f"Error transforming enhanced_plan: {str(e)}")
        # Return original data if transformation fails
        return enhanced_plan

def transform_ai_insights_for_ui(ai_insights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform ai_insights data structure to match UI expectations.
    
    Args:
        ai_insights: The original ai_insights data structure
        
    Returns:
        Transformed ai_insights
    """
    try:
        if not ai_insights:
            logger.warning("AI insights is empty or None")
            return {}
            
        # Check if ai_insights already has the expected structure
        if isinstance(ai_insights, list):
            logger.info("AI insights is already in array format")
            return ai_insights
            
        # Check if ai_insights has the nested structure
        if isinstance(ai_insights, dict) and "recommendations" in ai_insights:
            recommendations = ai_insights.get("recommendations", [])
            logger.info(f"Transforming ai_insights: extracted {len(recommendations)} recommendations")
            return recommendations
            
        # If ai_insights is a dict but doesn't have recommendations, return as is
        logger.warning("AI insights doesn't have expected structure, returning as is")
        return ai_insights
        
    except Exception as e:
        logger.error(f"Error transforming ai_insights: {str(e)}")
        # Return original data if transformation fails
        return ai_insights

def transform_recommendation_for_ui(recommendation: Dict[str, Any], enable_transformation: bool = True) -> Dict[str, Any]:
    """
    Transform a complete recommendation object for UI compatibility.
    
    Args:
        recommendation: The original recommendation data
        enable_transformation: Whether to apply transformation (for easy reversion)
        
    Returns:
        Transformed recommendation data
    """
    try:
        if not enable_transformation:
            logger.info("Transformation disabled, returning original data")
            return recommendation
            
        if not recommendation:
            logger.warning("Recommendation is empty or None")
            return recommendation
            
        # Create a copy to avoid modifying the original
        transformed = recommendation.copy()
        
        # Transform base_plan
        if "base_plan" in transformed:
            transformed["base_plan"] = transform_base_plan_for_ui(transformed["base_plan"])
            
        # Transform enhanced_plan
        if "enhanced_plan" in transformed:
            transformed["enhanced_plan"] = transform_enhanced_plan_for_ui(transformed["enhanced_plan"])
            
        # Transform ai_insights
        if "ai_insights" in transformed:
            transformed["ai_insights"] = transform_ai_insights_for_ui(transformed["ai_insights"])
            
        logger.info("Successfully transformed recommendation for UI")
        return transformed
        
    except Exception as e:
        logger.error(f"Error transforming recommendation: {str(e)}")
        # Return original data if transformation fails
        return recommendation
