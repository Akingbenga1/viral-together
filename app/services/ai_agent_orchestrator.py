from typing import Dict, Any, List
from datetime import datetime
from app.services.agent_coordinator_service import AgentCoordinatorService
from app.services.vector_db import VectorDatabaseService
from app.services.agent_response_service import AgentResponseService
from app.core.dependencies import get_db, get_vector_db, get_agent_coordinator_service

class AIAgentOrchestrator:
    def __init__(self):
        self.vector_db = VectorDatabaseService()
        
    async def get_agent_recommendations(self, user_profile: Dict[str, Any], 
                                      analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI agent recommendations using coordination service"""
        
        # Get dependencies
        db = get_db()
        vector_db = get_vector_db()
        coordinator = get_agent_coordinator_service(db, vector_db)
        
        # Create comprehensive prompt for AI analysis
        analysis_prompt = await self._create_analysis_prompt(user_profile, analysis_result)
        
        # Store analysis context in vector DB
        await self.vector_db.store_user_conversation(
            user_id=user_profile["user"].id,
            message=analysis_prompt,
            message_type="analysis_request",
            metadata={
                "analysis_type": "influencer_profile",
                "timestamp": analysis_result["analysis_timestamp"].isoformat(),
                "improvement_areas": analysis_result["improvement_areas"]
            }
        )
        
        # 1. CREATE COORDINATION SESSION using existing method
        coordination_uuid = await coordinator.create_coordination_session(
            user_id=user_profile["user"].id,
            task_type="influencer_analysis",
            initial_context={
                "analysis_result": analysis_result,
                "user_profile": {
                    "user_id": user_profile["user"].id,
                    "username": user_profile["user"].username,
                    "influencer_data": user_profile["influencer"] is not None
                }
            }
        )
        
        # 2. GET AVAILABLE AGENTS using existing method
        available_agents = await coordinator.get_available_agents(
            user_id=user_profile["user"].id,
            task_requirements={"capability": "analysis"}
        )
        
        if not available_agents:
            # Fallback: get any active agents for the user
            available_agents = await coordinator.get_available_agents(
                user_id=user_profile["user"].id,
                task_requirements={}
            )
        
        if not available_agents:
            return {
                "error": "No available agents found for user",
                "coordination_uuid": coordination_uuid,
                "agent_responses": []
            }
        
        # 3. ASSIGN TASKS TO AGENTS using existing method
        agent_tasks = []
        for agent in available_agents:
            task_assigned = await coordinator.assign_task_to_agent(
                coordination_uuid=coordination_uuid,
                agent_id=agent.id,
                task_details={
                    "prompt": analysis_prompt,
                    "agent_type": agent.agent_type,
                    "capabilities": agent.capabilities
                }
            )
            
            if task_assigned:
                agent_tasks.append({
                    "agent_id": agent.id,
                    "agent_type": agent.agent_type,
                    "capabilities": agent.capabilities,
                    "task_assigned": True
                })
        
        # 4. EXECUTE AGENT ANALYSIS with proper context
        agent_responses = []
        for task in agent_tasks:
            try:
                # Get context using existing method
                context = await coordinator.get_context_for_agent_task(
                    user_id=user_profile["user"].id,
                    current_prompt=analysis_prompt,
                    agent_id=task["agent_id"],
                    context_window=10
                )
                
                # Execute agent task (this would call the actual AI model)
                response = await self._execute_agent_task(
                    agent_id=task["agent_id"],
                    prompt=analysis_prompt,
                    context=context
                )
                
                # Record agent response
                await self._record_agent_response(
                    agent_id=task["agent_id"],
                    task_id=f"analysis_{user_profile['user'].id}_{datetime.now().timestamp()}",
                    response=response,
                    response_type="influencer_analysis"
                )
                
                agent_responses.append({
                    "agent_id": task["agent_id"],
                    "agent_type": task["agent_type"],
                    "focus_area": self._get_focus_area(task["agent_type"]),
                    "response": response,
                    "status": "success",
                    "context_used": context
                })
                
            except Exception as e:
                agent_responses.append({
                    "agent_id": task["agent_id"],
                    "agent_type": task["agent_type"],
                    "focus_area": "general",
                    "response": f"Error: {str(e)}",
                    "status": "error"
                })
        
        # 5. HANDLE AGENT HANDOFFS if needed
        handoff_results = await self._handle_agent_handoffs(
            coordinator=coordinator,
            coordination_uuid=coordination_uuid,
            agent_responses=agent_responses,
            user_profile=user_profile
        )
        
        # 6. COORDINATE AGENTS using existing method
        coordination_result = await coordinator.coordinate_agents(
            coordination_uuid=coordination_uuid,
            task={
                "type": "influencer_analysis",
                "agent_responses": agent_responses,
                "handoff_results": handoff_results
            }
        )
        
        # 7. RESOLVE CONFLICTS if any using existing method
        conflicts = self._identify_conflicts(agent_responses)
        conflict_resolution = None
        
        if conflicts:
            conflict_resolution = await coordinator.resolve_agent_conflicts(
                coordination_uuid=coordination_uuid,
                conflict_data=conflicts
            )
        
        return {
            "coordination_uuid": coordination_uuid,
            "available_agents": len(available_agents),
            "agent_tasks": agent_tasks,
            "agent_responses": agent_responses,
            "handoff_results": handoff_results,
            "coordination_result": coordination_result,
            "conflict_resolution": conflict_resolution,
            "analysis_prompt": analysis_prompt,
            "timestamp": datetime.now()
        }
        
    async def _create_analysis_prompt(self, user_profile: Dict[str, Any], 
                                    analysis_result: Dict[str, Any]) -> str:
        """Create comprehensive analysis prompt"""
        
        prompt = f"""
        INFLUENCER PROFILE ANALYSIS REQUEST
        
        User ID: {user_profile['user'].id}
        Username: {user_profile['user'].username}
        Email: {user_profile['user'].email}
        
        INFLUENCER PROFILE:
        - Primary Audience: {analysis_result['audience_insights'].get('primary_audience', 'N/A')}
        - Age Range: {analysis_result['audience_insights'].get('age_range', 'N/A')}
        - Geographic Focus: {analysis_result['audience_insights'].get('geographic_focus', 'N/A')}
        - Interests: {', '.join(analysis_result['audience_insights'].get('interests', []))}
        
        PERFORMANCE METRICS:
        - Engagement Rate: {analysis_result['performance_metrics'].get('engagement_rate', 0):.2f}%
        - Follower Growth: {analysis_result['performance_metrics'].get('follower_growth', 0)}
        - Reach: {analysis_result['performance_metrics'].get('reach', 0)}
        
        FINANCIAL ANALYSIS:
        - Total Revenue: ${analysis_result['financial_analysis'].get('total_revenue', 0)}
        - Average Rate: ${analysis_result['financial_analysis'].get('average_rate', 0)}
        - Rate Cards: {analysis_result['financial_analysis'].get('rate_cards_count', 0)}
        
        CONTENT ANALYSIS:
        - Consistency Score: {analysis_result['content_analysis'].get('consistency_score', 0)}/100
        - Posting Frequency: {analysis_result['content_analysis'].get('posting_frequency', 0)} posts/day
        - Recent Posts: {analysis_result['content_analysis'].get('recent_posts', 0)}
        
        IMPROVEMENT AREAS IDENTIFIED:
        {', '.join(analysis_result['improvement_areas'])}
        
        RECOMMENDATION PRIORITIES:
        {', '.join(analysis_result['recommendation_priorities'])}
        
        TASK: Based on this comprehensive profile analysis, provide detailed recommendations for:
        1. Monthly social media content strategy
        2. Audience engagement optimization
        3. Content posting schedule
        4. Pricing strategy improvements
        5. Growth tactics and goals
        6. Performance tracking metrics
        
        Please provide actionable, specific recommendations that will help this influencer achieve success.
        """
        
        return prompt
        
    async def _execute_agent_task(self, agent_id: int, prompt: str, context: Dict[str, Any]) -> str:
        """Execute agent task (simulated AI response)"""
        # This would integrate with your actual AI model (Ollama, etc.)
        # For now, return a simulated response based on agent type
        
        agent_type = context.get("agent_metadata", {}).get("agent_type", "general")
        
        if "marketing" in agent_type.lower():
            return """
            MARKETING SPECIALIST RECOMMENDATIONS:
            
            1. CONTENT STRATEGY:
            - Focus on high-engagement content types (polls, questions, behind-the-scenes)
            - Implement consistent posting schedule (5-6 posts per week)
            - Use trending hashtags strategically
            
            2. AUDIENCE ENGAGEMENT:
            - Respond to comments within 2 hours
            - Create interactive stories and polls
            - Host weekly Q&A sessions
            
            3. GROWTH TACTICS:
            - Collaborate with complementary influencers
            - Cross-promote on multiple platforms
            - Use user-generated content campaigns
            """
        elif "analytics" in agent_type.lower():
            return """
            ANALYTICS SPECIALIST INSIGHTS:
            
            1. PERFORMANCE METRICS:
            - Current engagement rate: 3.2% (industry average: 4.5%)
            - Follower growth: 15% monthly (good)
            - Content consistency: 70% (needs improvement)
            
            2. OPTIMIZATION OPPORTUNITIES:
            - Post timing: Best engagement between 6-9 PM
            - Content type: Video content performs 40% better
            - Hashtag strategy: Use 15-20 relevant hashtags
            
            3. GOAL SETTING:
            - Target engagement rate: 5% by month 3
            - Follower growth target: 20% monthly
            - Revenue increase: 30% through optimized pricing
            """
        else:
            return """
            GENERAL ASSISTANT RECOMMENDATIONS:
            
            1. OVERALL STRATEGY:
            - Develop a unique personal brand
            - Focus on authentic, valuable content
            - Build genuine relationships with audience
            
            2. CONTENT PLANNING:
            - Create content calendar with themes
            - Mix educational, entertaining, and promotional content
            - Maintain consistent visual style
            
            3. SUCCESS METRICS:
            - Track engagement rate improvements
            - Monitor follower quality (not just quantity)
            - Measure brand partnership inquiries
            """
        
    async def _record_agent_response(self, agent_id: int, task_id: str, response: str, response_type: str):
        """Record agent response using response service"""
        response_service = AgentResponseService()
        await response_service.record_agent_response(
            agent_id=agent_id,
            task_id=task_id,
            response=response,
            response_type=response_type
        )
        
    async def _handle_agent_handoffs(self, coordinator: AgentCoordinatorService, 
                                   coordination_uuid: str, agent_responses: List[Dict], 
                                   user_profile: Dict[str, Any]) -> List[Dict]:
        """Handle agent handoffs when specialized analysis is needed"""
        
        handoff_results = []
        
        # Check if any agent needs to handoff to a specialist
        for response in agent_responses:
            if response["status"] == "success":
                # Example: Marketing agent hands off to analytics specialist
                if "marketing" in response["agent_type"].lower():
                    # Look for analytics specialist
                    analytics_agents = await coordinator.get_available_agents(
                        user_id=user_profile["user"].id,
                        task_requirements={"capability": "analytics"}
                    )
                    
                    if analytics_agents:
                        handoff_success = await coordinator.handoff_task(
                            coordination_uuid=coordination_uuid,
                            from_agent_id=response["agent_id"],
                            to_agent_id=analytics_agents[0].id,
                            handoff_data={
                                "reason": "detailed_analytics_required",
                                "previous_analysis": response["response"],
                                "specialization_needed": "performance_metrics"
                            }
                        )
                        
                        if handoff_success:
                            handoff_results.append({
                                "from_agent": response["agent_id"],
                                "to_agent": analytics_agents[0].id,
                                "reason": "analytics_specialization",
                                "status": "success"
                            })
        
        return handoff_results
        
    def _identify_conflicts(self, agent_responses: List[Dict]) -> List[Dict]:
        """Identify conflicts between agent recommendations"""
        
        conflicts = []
        
        # Example: Check for conflicting pricing recommendations
        pricing_recommendations = []
        for response in agent_responses:
            if "pricing" in response["response"].lower():
                pricing_recommendations.append({
                    "agent_id": response["agent_id"],
                    "agent_type": response["agent_type"],
                    "recommendation": response["response"]
                })
        
        if len(pricing_recommendations) > 1:
            # Check for significant differences in pricing advice
            conflicts.append({
                "type": "pricing_conflict",
                "agents_involved": [pr["agent_id"] for pr in pricing_recommendations],
                "conflict_description": "Multiple agents provided conflicting pricing strategies",
                "severity": "medium"
            })
        
        return conflicts
        
    def _get_focus_area(self, agent_type: str) -> str:
        """Get focus area based on agent type"""
        if "marketing" in agent_type.lower():
            return "marketing_strategy"
        elif "analytics" in agent_type.lower():
            return "performance_analysis"
        elif "strategy" in agent_type.lower():
            return "overall_strategy"
        else:
            return "general_analysis"
