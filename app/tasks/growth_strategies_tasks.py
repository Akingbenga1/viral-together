from celery import Celery
from sqlalchemy import text
from app.db.session import SessionLocal
import logging
import json

logger = logging.getLogger(__name__)

# Initialize Celery app (assuming it's already configured)
from app.core.celery_app import celery_app

@celery_app.task(bind=True, name="generate_growth_strategies")
def generate_growth_strategies_task(self, influencer_id: int, recommendation_id: int = None):
    """
    Celery task to generate growth strategies for an influencer in the background
    Uses synchronous database operations to avoid connection conflicts
    """
    import asyncio
    from app.services.growth_strategies_service import GrowthStrategiesService
    
    # Add comprehensive logging
    logger.info(f"CELERY TASK STARTED: generate_growth_strategies_task")
    logger.info(f"Task ID: {self.request.id}")
    logger.info(f"Influencer ID: {influencer_id}")
    logger.info(f"Recommendation ID: {recommendation_id}")
    
    try:
        logger.info(f"STEP 1: Starting growth strategies generation for influencer_id: {influencer_id}")
        
        # Update task status (only if running in Celery context)
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 0, 'total': 100, 'status': 'Starting AI processing...'}
            )
            logger.info(f"Task state updated: PROGRESS (0/100) - Starting AI processing...")
        
        # Initialize the service
        logger.info(f"STEP 2: Initializing GrowthStrategiesService")
        service = GrowthStrategiesService()
        logger.info(f"Service initialized successfully")
        
        # Update progress (only if running in Celery context)
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 20, 'total': 100, 'status': 'Fetching recommendation data...'}
            )
            logger.info(f"Task state updated: PROGRESS (20/100) - Fetching recommendation data...")
        
        # Step 1: Get recommendation data using synchronous database operations
        logger.info(f"STEP 3: Fetching recommendation data for influencer_id: {influencer_id}")
        
        # Use synchronous database operations to avoid connection conflicts
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Create a synchronous engine for Celery tasks
        engine = create_engine("postgresql://postgres:password@localhost/viral_together")
        Session = sessionmaker(bind=engine)
        
        with Session() as db:
            # Get user_id from influencer_id
            user_query = text("SELECT user_id FROM influencers WHERE id = :influencer_id")
            user_result = db.execute(user_query, {"influencer_id": influencer_id})
            user_id = user_result.scalar()
            
            if not user_id:
                logger.error(f"No user found for influencer_id: {influencer_id}")
                if hasattr(self, 'request') and self.request.id:
                    self.update_state(
                        state='FAILURE',
                        meta={'error': 'NO_USER_FOUND', 'influencer_id': influencer_id}
                    )
                return {'status': 'FAILURE', 'error': 'NO_USER_FOUND', 'influencer_id': influencer_id}
            
            # Get recommendation data
            if recommendation_id:
                rec_query = text("""
                    SELECT id, user_id, base_plan, enhanced_plan, ai_insights, 
                           performance_goals, pricing_recommendations, monthly_schedule
                    FROM influencer_recommendations 
                    WHERE id = :rec_id AND user_id = :user_id
                """)
                rec_result = db.execute(rec_query, {"rec_id": recommendation_id, "user_id": user_id})
            else:
                rec_query = text("""
                    SELECT id, user_id, base_plan, enhanced_plan, ai_insights, 
                           performance_goals, pricing_recommendations, monthly_schedule
                    FROM influencer_recommendations 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                rec_result = db.execute(rec_query, {"user_id": user_id})
            
            recommendation_row = rec_result.fetchone()
            
            if not recommendation_row:
                logger.error(f"No recommendation data found for influencer_id: {influencer_id}")
                if hasattr(self, 'request') and self.request.id:
                    self.update_state(
                        state='FAILURE',
                        meta={'error': 'NO_RECOMMENDATION_DATA', 'influencer_id': influencer_id}
                    )
                return {'status': 'FAILURE', 'error': 'NO_RECOMMENDATION_DATA', 'influencer_id': influencer_id}
            
            # Convert to dictionary
            recommendation_data = {
                'id': recommendation_row.id,
                'influencer_id': influencer_id,
                'user_id': user_id,
                'base_plan': recommendation_row.base_plan,
                'enhanced_plan': recommendation_row.enhanced_plan,
                'ai_insights': recommendation_row.ai_insights,
                'performance_goals': recommendation_row.performance_goals,
                'pricing_recommendations': recommendation_row.pricing_recommendations,
                'monthly_schedule': recommendation_row.monthly_schedule
            }
        
        logger.info(f"Recommendation data fetched: {recommendation_data is not None}")
        logger.info(f"Recommendation ID: {recommendation_data.get('id')}")
        logger.info(f"User ID: {recommendation_data.get('user_id')}")
        
        # Update progress (only if running in Celery context)
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 40, 'total': 100, 'status': 'Running AI agents...'}
            )
            logger.info(f"Task state updated: PROGRESS (40/100) - Running AI agents...")
        
        # Step 2: Generate strategies using AI agent (async operation)
        logger.info(f"STEP 4: Starting AI agent execution for influencer_id: {influencer_id}")
        
        # Use asyncio.run for AI agent execution only
        async def generate_strategies_async():
            return await service._generate_growth_strategies(recommendation_data)
        
        strategies = asyncio.run(generate_strategies_async())
        
        logger.info(f"AI Agent execution completed!")
        logger.info(f"Strategies generated: {strategies is not None}")
        if strategies:
            logger.info(f"Strategy keys: {list(strategies.keys())}")
            for key, value in strategies.items():
                if isinstance(value, list):
                    logger.info(f"{key}: {len(value)} items")
                else:
                    logger.info(f"{key}: {type(value)}")
        else:
            logger.warning(f"No strategies generated by AI agent")
            if hasattr(self, 'request') and self.request.id:
                self.update_state(
                    state='FAILURE',
                    meta={'error': 'NO_STRATEGIES_GENERATED', 'influencer_id': influencer_id}
                )
            return {'status': 'FAILURE', 'error': 'NO_STRATEGIES_GENERATED', 'influencer_id': influencer_id}
        
        # Update progress (only if running in Celery context)
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Saving strategies to database...'}
            )
            logger.info(f"Task state updated: PROGRESS (80/100) - Saving strategies to database...")
        
        # Step 3: Save to database using synchronous operations
        logger.info(f"STEP 5: Saving strategies to database")
        logger.info(f"Saving for influencer_id: {influencer_id}, recommendation_id: {recommendation_data['id']}")
        
        # Use synchronous database operations to save
        with Session() as db:
            # Check if summary already exists
            check_query = text("""
                SELECT id FROM influencer_recommendation_summaries 
                WHERE influencer_recommendation_id = :rec_id AND influencer_id = :inf_id
            """)
            existing = db.execute(check_query, {"rec_id": recommendation_data['id'], "inf_id": influencer_id}).fetchone()
            
            if existing:
                # Update existing record
                update_query = text("""
                    UPDATE influencer_recommendation_summaries 
                    SET more_followers = :more_followers,
                        content_ideas = :content_ideas,
                        social_profiles = :social_profiles,
                        influencer_collab = :influencer_collab,
                        business_collab = :business_collab,
                        content_scripts = :content_scripts,
                        updated_at = NOW()
                    WHERE influencer_recommendation_id = :rec_id AND influencer_id = :inf_id
                """)
                db.execute(update_query, {
                    "rec_id": recommendation_data['id'],
                    "inf_id": influencer_id,
                    "more_followers": json.dumps(strategies.get('more_followers', [])),
                    "content_ideas": json.dumps(strategies.get('content_ideas', [])),
                    "social_profiles": json.dumps(strategies.get('social_profiles', [])),
                    "influencer_collab": json.dumps(strategies.get('influencer_collab', [])),
                    "business_collab": json.dumps(strategies.get('business_collab', [])),
                    "content_scripts": json.dumps(strategies.get('content_scripts', []))
                })
                logger.info(f"Updated existing summary record")
            else:
                # Insert new record
                insert_query = text("""
                    INSERT INTO influencer_recommendation_summaries 
                    (influencer_recommendation_id, influencer_id, more_followers, content_ideas, 
                     social_profiles, influencer_collab, business_collab, content_scripts, created_at)
                    VALUES (:rec_id, :inf_id, :more_followers, :content_ideas, :social_profiles, 
                            :influencer_collab, :business_collab, :content_scripts, NOW())
                """)
                db.execute(insert_query, {
                    "rec_id": recommendation_data['id'],
                    "inf_id": influencer_id,
                    "more_followers": json.dumps(strategies.get('more_followers', [])),
                    "content_ideas": json.dumps(strategies.get('content_ideas', [])),
                    "social_profiles": json.dumps(strategies.get('social_profiles', [])),
                    "influencer_collab": json.dumps(strategies.get('influencer_collab', [])),
                    "business_collab": json.dumps(strategies.get('business_collab', [])),
                    "content_scripts": json.dumps(strategies.get('content_scripts', []))
                })
                logger.info(f"Inserted new summary record")
            
            db.commit()
            logger.info(f"Database save completed successfully")
        
        # Update progress (only if running in Celery context)
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Completed successfully!'}
            )
            logger.info(f"Task state updated: PROGRESS (100/100) - Completed successfully!")
        logger.info(f"SUCCESS: Growth strategies generated for influencer_id: {influencer_id}")
        
        return {
            'status': 'SUCCESS',
            'influencer_id': influencer_id,
            'recommendation_id': recommendation_data['id'],
            'message': 'Growth strategies generated successfully'
        }
        
    except Exception as exc:
        logger.error(f"ERROR in Celery task for influencer_id {influencer_id}: {str(exc)}")
        logger.error(f"Error type: {type(exc).__name__}")
        logger.error(f"Error details: {str(exc)}")
        if hasattr(self, 'request') and self.request.id:
            self.update_state(
                state='FAILURE',
                meta={'error': str(exc), 'influencer_id': influencer_id}
            )
        raise exc

@celery_app.task(name="check_processing_status")
def check_processing_status(influencer_id: int):
    """
    Check if growth strategies are currently being processed for an influencer
    """
    try:
        # Check if there are any active tasks for this influencer
        active_tasks = celery_app.control.inspect().active()
        
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    if (task['name'] == 'generate_growth_strategies' and 
                        task['args'] and 
                        len(task['args']) > 0 and 
                        task['args'][0] == influencer_id):
                        return {
                            'is_processing': True,
                            'task_id': task['id'],
                            'status': task['state']
                        }
        
        return {'is_processing': False}
        
    except Exception as exc:
        logger.error(f"Error checking processing status for influencer_id {influencer_id}: {str(exc)}")
        return {'is_processing': False, 'error': str(exc)}