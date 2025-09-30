from typing import Dict, Any, List
from datetime import datetime
import logging
from app.services.agent_coordinator_service import AgentCoordinatorService
from app.services.vector_db import VectorDatabaseService
from app.services.agent_response_service import AgentResponseService
from app.services.ai_agent_service import AIAgentService
from app.core.dependencies import get_db, get_vector_db, get_agent_coordinator_service

logger = logging.getLogger(__name__)

class AIAgentOrchestrator:
    def __init__(self):
        self.vector_db = VectorDatabaseService()
        self.ai_agent_service = AIAgentService()
    
    def _extract_user_fields(self, user_obj: Any) -> Dict[str, Any]:
        """Return {'id', 'username', 'email'} from either an object or a dict.
        This makes the orchestrator tolerant to Celery serialization (dict) and in-process objects.
        """
        if user_obj is None:
            return {"id": 0, "username": "Anonymous", "email": ""}
        if isinstance(user_obj, dict):
            return {
                "id": user_obj.get("id") or user_obj.get("user_id") or 0,
                "username": user_obj.get("username") or "Anonymous",
                "email": user_obj.get("email") or "",
            }
        # Fallback to attribute access
        user_id = getattr(user_obj, "id", 0)
        username = getattr(user_obj, "username", "Anonymous")
        email = getattr(user_obj, "email", "")
        return {"id": user_id, "username": username, "email": email}
        
    async def get_agent_recommendations(self, user_profile: Dict[str, Any], 
                                      analysis_result: Dict[str, Any], 
                                      db_session=None) -> Dict[str, Any]:
        """Get AI agent recommendations using coordination service with real Ollama integration"""
        
        try:
            # Create services directly instead of using dependency functions
            vector_db = VectorDatabaseService()
            
            # Create async database session if none provided
            if db_session is None:
                from app.db.session import SessionLocal
                db_session = SessionLocal()
            
            # Check if db_session is async or sync
            from sqlalchemy.ext.asyncio import AsyncSession
            if isinstance(db_session, AsyncSession):
                coordinator = AgentCoordinatorService(db_session, vector_db)  # Pass the async database session
            else:
                # Convert sync session to async session
                from app.db.session import SessionLocal as AsyncSessionLocal
                async_db_session = AsyncSessionLocal()
                coordinator = AgentCoordinatorService(async_db_session, vector_db)  # Pass the async database session
            
            # Create comprehensive prompt for AI analysis
            analysis_prompt = self._create_analysis_prompt(user_profile, analysis_result)
            
            # Normalize user fields (robust to dict/object forms)
            user_fields = self._extract_user_fields(user_profile.get("user") if user_profile else None)
            user_id = user_fields["id"]
            username = user_fields["username"]
            email = user_fields["email"]
            # Store analysis context in vector DB
            logger.info(f"ORCHESTRATOR_DEBUG: user_profile type={type(user_profile)}")
            logger.info(f"ORCHESTRATOR_DEBUG: normalized user fields: id={user_id}, username={username}")
            
            self.vector_db.store_user_conversation(
                user_id=user_id,
                conversation_text=analysis_prompt,
                conversation_type="analysis_request",
                metadata={
                    "analysis_type": "influencer_profile",
                    "timestamp": analysis_result["analysis_timestamp"].isoformat(),
                    "improvement_areas": analysis_result["improvement_areas"]
                }
            )
            
            # 1. CREATE COORDINATION SESSION using existing method
            coordination_uuid = await coordinator.create_coordination_session(
                user_id=user_id,
                task_type="influencer_analysis",
                initial_context={
                    "analysis_result": analysis_result,
                    "user_profile": {
                        "user_id": user_id,
                        "username": username,
                        "influencer_data": user_profile["influencer"] is not None
                    }
                }
            )
            
            # 2. GET AVAILABLE AGENTS using existing method
            logger.info(f"ORCHESTRATOR_DEBUG: About to call get_available_agents with user_id={user_id}")
            try:
                available_agents = await coordinator.get_available_agents(
                    user_id=user_id,
                    task_requirements={
                        "capability": "audience_analysis",
                        "task_description": "Comprehensive influencer profile analysis and strategy development",
                        "user_context": {
                            "user_id": user_id,
                            "username": username,
                            "influencer_data": user_profile["influencer"] is not None,
                            "analysis_type": "influencer_profile",
                            "improvement_areas": analysis_result["improvement_areas"],
                            "recommendation_priorities": analysis_result["recommendation_priorities"]
                        }
                    }
                )
                logger.info(f"ORCHESTRATOR_DEBUG: Got {len(available_agents)} available agents")
            except Exception as agents_error:
                logger.error(f"ORCHESTRATOR_AGENTS_ERROR: Error getting available agents: {agents_error}")
                raise agents_error
            
            print(f"DEBUG: Found {len(available_agents)} agents with audience_analysis capability")
            
            if not available_agents:
                # Fallback: get any active agents for the user
                available_agents = await coordinator.get_available_agents(
                    user_id=user_id,
                    task_requirements={
                        "task_description": "General influencer analysis and recommendations",
                        "user_context": {
                            "user_id": user_id,
                            "username": username,
                            "influencer_data": user_profile["influencer"] is not None
                        }
                    }
                )
                print(f"DEBUG: Fallback found {len(available_agents)} agents without capability filter")
            
            if not available_agents:
                return {
                    "error": "No available agents found for user",
                    "coordination_uuid": coordination_uuid,
                    "agent_responses": []
                }
            
            # 3. ASSIGN TASKS TO AGENTS using existing method
            agent_tasks = []
            for agent in available_agents:
                # Handle both object and dict forms for agents
                agent_id = agent.id if hasattr(agent, 'id') else agent.get('id')
                agent_type = agent.agent_type if hasattr(agent, 'agent_type') else agent.get('agent_type')
                capabilities = agent.capabilities if hasattr(agent, 'capabilities') else agent.get('capabilities')
                
                logger.info(f"DEBUG_AGENT: agent type={type(agent)}, agent_id={agent_id}, agent_type={agent_type}")
                task_assigned = await coordinator.assign_task_to_agent(
                    coordination_uuid=coordination_uuid,
                    agent_id=agent_id,
                    task_details={
                        "prompt": analysis_prompt,
                        "agent_type": agent_type,
                        "capabilities": capabilities
                    }
                )
                
                if task_assigned:
                    agent_tasks.append({
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "capabilities": capabilities,
                        "task_assigned": True
                    })
            
            # 4. EXECUTE AGENT ANALYSIS with real Ollama integration
            agent_responses = []
            for task in agent_tasks:
                try:
                    # Get context using existing method
                    context = await coordinator.get_context_for_agent_task(
                        user_id=user_id,
                        current_prompt=analysis_prompt,
                        agent_id=task["agent_id"],
                        context_window=10
                    )
                    
                    # Execute agent task using the new AI agent service
                    response = await self.ai_agent_service.execute_agent_task(
                        agent_id=task["agent_id"],
                        prompt=analysis_prompt,
                        context=context,
                        agent_type=task["agent_type"]
                    )
                    
                    # Record agent response
                    self._record_agent_response(
                        agent_id=task["agent_id"],
                        task_id=f"analysis_{user_id}_{datetime.now().timestamp()}",
                        response=response["response"],
                        response_type="influencer_analysis"
                    )
                    
                    agent_responses.append(response)
                    
                except Exception as e:
                    print(f"❌ Error executing agent task {task['agent_id']}: {str(e)}")
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
            
        except Exception as e:
            print(f"Error in get_agent_recommendations: {str(e)}")
            # Return a fallback response instead of crashing
            return {
                "error": f"Failed to get agent recommendations: {str(e)}",
                "coordination_uuid": None,
                "available_agents": 0,
                "agent_tasks": [],
                "agent_responses": [],
                "handoff_results": [],
                "coordination_result": None,
                "conflict_resolution": None,
                "analysis_prompt": "Error occurred during prompt creation",
                "timestamp": datetime.now()
            }
        
    def _create_analysis_prompt(self, user_profile: Dict[str, Any], 
                                   analysis_result: Dict[str, Any]) -> str:
        """Create comprehensive analysis prompt"""
        
        # Normalize user fields for prompt creation too
        user_fields = self._extract_user_fields(user_profile.get("user") if user_profile else None)
        uid, uname, uemail = user_fields["id"], user_fields["username"], user_fields["email"]

        prompt = f"""
        INFLUENCER PROFILE ANALYSIS REQUEST
        
        User ID: {uid}
        Username: {uname}
        Email: {uemail}
        
        INFLUENCER PROFILE:
        - Location: {analysis_result['audience_insights'].get('location', 'N/A')}
        - Languages: {analysis_result['audience_insights'].get('languages', 'N/A')}
        - Base Country ID: {analysis_result['audience_insights'].get('base_country_id', 'N/A')}
        - Availability: {analysis_result['audience_insights'].get('availability', 'N/A')}
        - Total Posts: {analysis_result['audience_insights'].get('total_posts', 0)}
        - Growth Rate: {analysis_result['audience_insights'].get('growth_rate', 0)}
        - Successful Campaigns: {analysis_result['audience_insights'].get('successful_campaigns', 0)}
        
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
        
    def _record_agent_response(self, agent_id: int, task_id: str, response: str, response_type: str):
        """Record agent response using response service"""
        # For now, we'll skip recording to avoid database dependency issues
        # In a full implementation, this would use proper dependency injection
        print(f"📝 Would record agent response: {agent_id} - {task_id} - {response_type}")
        # response_service = AgentResponseService()
        # await response_service.record_agent_response(
        #     agent_id=agent_id,
        #     task_id=task_id,
        #     response=response,
        #     response_type=response_type
        # )
        
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
                    user_fields = self._extract_user_fields(user_profile.get("user") if user_profile else None)
                    user_id = user_fields["id"]
                    analytics_agents = await coordinator.get_available_agents(
                        user_id=user_id,
                        task_requirements={
                            "capability": "analytics",
                            "task_description": "Detailed analytics and performance analysis",
                            "user_context": {
                                "user_id": user_id,
                                "handoff_reason": "detailed_analytics_required",
                                "previous_analysis": response["response"],
                                "specialization_needed": "performance_metrics"
                            }
                        }
                    )
                    
                    if analytics_agents:
                        # Handle both object and dict forms for agents
                        to_agent_id = analytics_agents[0].id if hasattr(analytics_agents[0], 'id') else analytics_agents[0].get('id')
                        handoff_success = await coordinator.handoff_task(
                            coordination_uuid=coordination_uuid,
                            from_agent_id=response["agent_id"],
                            to_agent_id=to_agent_id,
                            handoff_data={
                                "reason": "analytics_specialization",
                                "previous_analysis": response["response"],
                                "specialization_needed": "performance_metrics"
                            }
                        )
                        
                        if handoff_success:
                            handoff_results.append({
                                "from_agent": response["agent_id"],
                                "to_agent": to_agent_id,
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
    
    def create_prompt_based_on_text_content(self, text_content: str, user_profile: Dict[str, Any] = None) -> str:
        """Create a generic prompt template based on user-provided text content"""
        
        # Create a simple, generic prompt that just contains the user input
        prompt = f"""
{text_content}
"""
        
        return prompt
    
    async def get_custom_text_recommendations(self, text_content: str, user_profile: Dict[str, Any] = None, 
                                            db_session=None) -> Dict[str, Any]:
        """Get AI agent recommendations for custom text content"""
        
        try:
            # Create services directly
            vector_db = VectorDatabaseService()
            coordinator = AgentCoordinatorService(db_session, vector_db)
            
            # Create custom prompt based on text content
            custom_prompt = self.create_prompt_based_on_text_content(text_content, user_profile)
            
            # Store custom analysis context in vector DB
            if user_profile and user_profile.get('user'):
                user_fields = self._extract_user_fields(user_profile.get("user"))
                user_id = user_fields["id"]
                self.vector_db.store_user_conversation(
                    user_id=user_id,
                    conversation_text=custom_prompt,
                    conversation_type="custom_text_analysis",
                    metadata={
                        "analysis_type": "custom_text",
                        "timestamp": datetime.now().isoformat(),
                        "content_length": len(text_content)
                    }
                )
            
            # Create coordination session
            user_fields = self._extract_user_fields(user_profile.get("user") if user_profile else None)
            user_id = user_fields["id"]
            username = user_fields["username"]
            coordination_uuid = await coordinator.create_coordination_session(
                user_id=user_id,
                task_type="custom_text_analysis",
                initial_context={
                    "text_content": text_content,
                    "user_profile": {
                        "user_id": user_id,
                        "username": username,
                        "has_influencer_data": user_profile.get("influencer") is not None if user_profile else False
                    }
                }
            )
            
            # Get available agents for custom text analysis
            available_agents = await coordinator.get_available_agents(
                user_id=user_id,
                task_requirements={
                    "task_description": f"Custom text analysis and recommendations for: {text_content[:100]}...",
                    "user_context": {
                        "user_id": user_id,
                        "username": username,
                        "content_type": "custom_text",
                        "content_length": len(text_content)
                    }
                }
            )
            
            if not available_agents:
                return {
                    "error": "No available agents found for custom text analysis",
                    "coordination_uuid": coordination_uuid,
                    "agent_responses": []
                }
            
            # Assign tasks to agents
            agent_tasks = []
            for agent in available_agents:
                # Handle both object and dict forms for agents
                agent_id = agent.id if hasattr(agent, 'id') else agent.get('id')
                agent_type = agent.agent_type if hasattr(agent, 'agent_type') else agent.get('agent_type')
                capabilities = agent.capabilities if hasattr(agent, 'capabilities') else agent.get('capabilities')
                
                task_assigned = await coordinator.assign_task_to_agent(
                    coordination_uuid=coordination_uuid,
                    agent_id=agent_id,
                    task_details={
                        "prompt": custom_prompt,
                        "agent_type": agent_type,
                        "capabilities": capabilities
                    }
                )
                
                if task_assigned:
                    agent_tasks.append({
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "capabilities": capabilities,
                        "task_assigned": True
                    })
            
            # Execute agent analysis
            agent_responses = []
            for task in agent_tasks:
                try:
                    # Get context for agent task
                    context = await coordinator.get_context_for_agent_task(
                        user_id=user_id,
                        current_prompt=custom_prompt,
                        agent_id=task["agent_id"],
                        context_window=10
                    )
                    
                    # Execute agent task
                    response = await self.ai_agent_service.execute_agent_task(
                        agent_id=task["agent_id"],
                        prompt=custom_prompt,
                        context=context,
                        agent_type=task["agent_type"]
                    )
                    
                    # Record agent response
                    self._record_agent_response(
                        agent_id=task["agent_id"],
                        task_id=f"custom_analysis_{datetime.now().timestamp()}",
                        response=response["response"],
                        response_type="custom_text_analysis"
                    )
                    
                    agent_responses.append(response)
                    
                except Exception as e:
                    print(f"❌ Error executing agent task {task['agent_id']}: {str(e)}")
                    agent_responses.append({
                        "agent_id": task["agent_id"],
                        "agent_type": task["agent_type"],
                        "focus_area": "general",
                        "response": f"Error: {str(e)}",
                        "status": "error"
                    })
            
            # Handle agent handoffs
            handoff_results = await self._handle_agent_handoffs(
                coordinator=coordinator,
                coordination_uuid=coordination_uuid,
                agent_responses=agent_responses,
                user_profile=user_profile or {}
            )
            
            # Coordinate agents
            coordination_result = await coordinator.coordinate_agents(
                coordination_uuid=coordination_uuid,
                task={
                    "type": "custom_text_analysis",
                    "agent_responses": agent_responses,
                    "handoff_results": handoff_results
                }
            )
            
            # Resolve conflicts
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
                "custom_prompt": custom_prompt,
                "text_content_length": len(text_content),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error in get_custom_text_recommendations: {str(e)}")
            return {
                "error": f"Failed to get custom text recommendations: {str(e)}",
                "coordination_uuid": None,
                "available_agents": 0,
                "agent_tasks": [],
                "agent_responses": [],
                "handoff_results": [],
                "coordination_result": None,
                "conflict_resolution": None,
                "custom_prompt": "Error occurred during prompt creation",
                "timestamp": datetime.now()
            }
