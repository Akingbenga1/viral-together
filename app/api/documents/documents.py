from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.services.document_generator import generate_document
from app.schemas.generated_documents import GeneratedDocument, GeneratedDocumentCreate
from app.db.models.generated_documents import GeneratedDocument as GeneratedDocumentModel
from app.db.models.document_templates import DocumentTemplate
from app.db.models.influencer import Influencer
from app.db.models.business import Business
from app.core.query_helpers import safe_scalar_one_or_none
from typing import Dict, Annotated, List, Any
from sqlalchemy import func
from types import SimpleNamespace
from datetime import datetime
from pydantic import BaseModel
import logging
import uuid
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.db.models.country import Country as CountryModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

class BusinessPlanRequest(BaseModel):
    influencer_id: int
    industry: str
    product: str
    countries: List[str]
    file_format: str = "pdf"

class SpecificCollaborationRequest(BaseModel):
    business_id: int
    influencer_id: int
    campaign_title: str
    campaign_description: str
    deliverables: List[str]
    compensation_amount: float
    campaign_duration: str
    content_requirements: str
    brand_guidelines: str = ""
    deadline: str
    file_format: str = "pdf"

class GeneralCollaborationRequest(BaseModel):
    business_id: int
    campaign_title: str
    campaign_description: str
    target_audience: str
    target_follower_range: str  # e.g., "10K-100K", "100K-1M"
    preferred_niches: List[str]  # e.g., ["fashion", "lifestyle", "tech"]
    deliverables: List[str]
    compensation_range: str  # e.g., "$500-$2000"
    campaign_duration: str
    content_requirements: str
    brand_guidelines: str = ""
    deadline: str
    target_countries: List[str] = ["United States"]
    file_format: str = "pdf"

class PublicCollaborationRequest(BaseModel):
    business_profile: Dict[str, Any]  # Business profile data from lines 19-28 of business.http
    campaign_title: str
    campaign_description: str
    target_audience: str
    target_follower_range: str
    preferred_niches: List[str]
    deliverables: List[str]
    compensation_range: str
    campaign_duration: str
    content_requirements: str
    brand_guidelines: str = ""
    deadline: str
    target_countries: List[str] = ["United States"]
    file_format: str = "pdf"

class MarketAnalysisRequest(BaseModel):
    business_profile: Dict[str, Any]  # Business profile data from lines 185-194 of documents.http

class SocialMediaPlanRequest(BaseModel):
    influencer_profile: Dict[str, Any]  # Influencer profile data from the form
    file_format: str = "pdf"

class InfluencerBusinessPlanRequest(BaseModel):
    influencer_profile: Dict[str, Any]  # Influencer profile data from the form
    file_format: str = "pdf"

@router.post("/generate", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_doc_async(
    request: GeneratedDocumentCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    skip_template_validation: Annotated[bool, Query(description="Skip template validation for development")] = False
):
    """Generate document asynchronously using background tasks"""
    
    # Create job record immediately with 'pending' status
    job_id = str(uuid.uuid4())
    
    new_doc = GeneratedDocumentModel(
        user_id=request.user_id,
        template_id=request.template_id,
        type="custom",
        subtype="generated", 
        influencer_id=request.influencer_id,
        business_id=request.business_id,
        promotion_id=request.promotion_id,
        collaboration_id=request.collaboration_id,
        parameters=request.parameters,
        file_path=f"pending_{job_id}",  # Placeholder
        generation_status='pending',  # Status tracking
        created_at=func.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Add background task for actual document generation
    background_tasks.add_task(
        generate_document_background,
        new_doc.id,
        request,
        skip_template_validation
    )
    
    logger.info(f"Started background document generation for document ID: {new_doc.id}")
    
    # Return immediately with job info
    return {
        "message": "Document generation started",
        "job_id": job_id,
        "document_id": new_doc.id,
        "status": "pending",
        "estimated_completion": "30-60 seconds",
        "check_status_url": f"/documents/{new_doc.id}/status",
        "download_url": f"/documents/{new_doc.id}/download"
    }


async def generate_document_background(
    document_id: int,
    request: GeneratedDocumentCreate,
    skip_template_validation: bool = False
):
    """Background task for document generation"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to 'processing'
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            logger.info(f"Starting background generation for document '{doc.type}' (ID: {document_id}) with format: {doc.parameters.get('file_format', 'unknown')}")
            
            # Template lookup (same logic as before)
            template = None
            template_type = "custom"
            template_subtype = "generated"
            
            if request.template_id and not skip_template_validation:
                try:
                    template_result = await db.execute(
                        select(DocumentTemplate).where(DocumentTemplate.id == request.template_id)
                    )
                    template = await safe_scalar_one_or_none(template_result)
                    
                    if template:
                        template_type = template.type
                        template_subtype = template.subtype
                        logger.info(f"Using template '{template.name}' (ID: {request.template_id}) for document generation")
                    else:
                        logger.warning(f"Template ID {request.template_id} not found, using fallback generation")
                        
                except Exception as e:
                    logger.error(f"Template lookup failed: {e}, continuing with fallback")
            
            # Create fallback template if needed
            if not template:
                template = SimpleNamespace(
                    id=request.template_id or 'fallback',
                    prompt_text=request.parameters.get('content', 'Generated document: {{title}}\n\nContent: {{content}}\n\nGenerated for user: {{user_id}}'),
                    default_parameters={},
                    file_format=request.parameters.get('file_format', 'pdf'),
                    type=template_type,
                    subtype=template_subtype
                )
                logger.info("Using fallback template generation for development")
            
            # Related data
            related_data = {
                'user_id': request.user_id,
                'influencer_id': request.influencer_id,
                'business_id': request.business_id,
                'promotion_id': request.promotion_id,
                'collaboration_id': request.collaboration_id
            }
            
            # Generate document (this is the time-consuming part)
            file_path = generate_document(template, request.parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.type = template_type
            doc.subtype = template_subtype
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            
            await db.commit()
            logger.info(f"Document '{doc.type}' (ID: {document_id}) generated successfully: {file_path}")
            
            # Optional: Send notification/webhook here
            # await send_completion_notification(doc)
            
        except Exception as e:
            logger.error(f"Background generation failed for document '{doc.type}' (ID: {document_id}): {e}")
            
            try:
                # Update with error status
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                                        logger.error(f"Failed to update error status for document '{doc.type}' (ID: {document_id}): {db_error}")


@router.post("/generate-business-plan", response_model=Dict)
async def generate_business_plan(
    request: BusinessPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a business plan for an influencer using their profile data and specified industry/product"""
    
    try:
        # Fetch influencer profile details
        influencer_result = await db.execute(
            select(Influencer).where(Influencer.id == request.influencer_id)
        )
        influencer = await safe_scalar_one_or_none(influencer_result)
        
        if not influencer:
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        # Construct business plan prompt using influencer profile
        countries_text = ", ".join(request.countries)
        
        business_plan_prompt = f"""
# Business Plan: {request.product} Promotion in {request.industry} Industry

# Influencer Profile
**Name:** {getattr(influencer, 'name', 'Professional Influencer')}
**Username:** {getattr(influencer, 'username', 'N/A')}
**Bio:** {getattr(influencer, 'bio', 'Social media influencer specializing in content creation')}
**Location:** {getattr(influencer, 'location', 'Global')}
**Follower Count:** {getattr(influencer, 'follower_count', 'N/A')}

# Campaign Overview
**Target Industry:** {request.industry}
**Product/Service:** {request.product}  
**Target Markets:** {countries_text}

# Business Objectives
Create a comprehensive business plan for promoting {request.product} in the {request.industry} industry across {countries_text}.

# Market Analysis
Analyze the {request.industry} market opportunities in {countries_text} and how this influencer's audience aligns with the target demographic.

# Marketing Strategy
Develop specific tactics leveraging the influencer's strengths and audience engagement patterns.Add examples with figures and data to backup your statement. Ensure the examples are included and listed.

# Content Strategy
Outline content types, posting schedule, and engagement tactics suitable for promoting {request.product}.Give 5 action steps examples. Ensure the examples are included and listed.

# Financial Projections
Include estimated costs, revenue projections, and ROI calculations for the campaign.

# Success Metrics
Define KPIs and measurement strategies for tracking campaign performance.Use figures to define the KPI expectations.Ensure the examples are included and listed.

# Implementation Timeline
Create a detailed timeline for campaign execution and milestones.

Generate a professional, detailed business plan based on this information.Provide data based examples
"""

        # Create template object for the business plan
        template = SimpleNamespace(
            id='business_plan_template',
            prompt_text=business_plan_prompt,
            file_format=request.file_format,
            type='business_plan',
            subtype='influencer_campaign'
        )
        
        # Parameters for document generation
        parameters = {
            'influencer_name': getattr(influencer, 'name', 'Professional Influencer'),
            'industry': request.industry,
            'product': request.product,
            'countries': countries_text,
            'file_format': request.file_format
        }
        
        # Related data
        related_data = {
            'influencer_id': request.influencer_id,
            'user_id': getattr(influencer, 'user_id', None)
        }
        
        # Generate the business plan document
        influencer_name = getattr(influencer, 'name', f'Influencer {request.influencer_id}')
        logger.info(f"Generating business plan for influencer '{influencer_name}' (ID: {request.influencer_id}) - {request.product} in {request.industry}")
        file_path = generate_document(template, parameters, related_data)
        
        # Create database record for the generated business plan
        new_doc = GeneratedDocumentModel(
            user_id=getattr(influencer, 'user_id', 1),
            template_id=None,
            type='business_plan',
            subtype='influencer_campaign',
            influencer_id=request.influencer_id,
            parameters=parameters,
            file_path=file_path,
            generation_status='completed',
            generated_at=func.now(),
            created_at=func.now()
        )
        
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        logger.info(f"Business plan for influencer '{influencer_name}' (ID: {request.influencer_id}) generated successfully: {file_path}")
        
        return {
            "message": "Business plan generated successfully",
            "document_id": new_doc.id,
            "file_path": file_path,
            "influencer_name": influencer_name,
            "industry": request.industry,
            "product": request.product,
            "target_countries": countries_text,
            "download_url": f"/documents/{new_doc.id}/download",
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating business plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate business plan: {str(e)}")


@router.post("/generate-collaboration-request-specific", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_specific_collaboration_request_async(
    request: SpecificCollaborationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a personalized collaboration request for a specific influencer"""
    
    # Validate business and influencer exist
    business_result = await db.execute(
        select(Business).where(Business.id == request.business_id)
    )
    business = await safe_scalar_one_or_none(business_result)
    
    influencer_result = await db.execute(
        select(Influencer).where(Influencer.id == request.influencer_id)
    )
    influencer = await safe_scalar_one_or_none(influencer_result)
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    # Create job record
    job_id = str(uuid.uuid4())
    
    new_doc = GeneratedDocumentModel(
        user_id=getattr(business, 'user_id', 1),
        template_id=None,
        type='collaboration_request',
        subtype='specific_influencer',
        business_id=request.business_id,
        influencer_id=request.influencer_id,
        parameters={
            'campaign_title': request.campaign_title,
            'campaign_description': request.campaign_description,
            'deliverables': request.deliverables,
            'compensation_amount': request.compensation_amount,
            'campaign_duration': request.campaign_duration,
            'content_requirements': request.content_requirements,
            'brand_guidelines': request.brand_guidelines,
            'deadline': request.deadline,
            'file_format': request.file_format
        },
        file_path=f"pending_{job_id}",
        generation_status='pending',
        created_at=func.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Add background task
    background_tasks.add_task(
        generate_specific_collaboration_background,
        new_doc.id,
        request
    )
    
    logger.info(f"Started specific collaboration request generation for document ID: {new_doc.id}")
    
    return {
        "message": "Specific collaboration request generation started",
        "job_id": job_id,
        "document_id": new_doc.id,
        "status": "pending",
        "business_name": getattr(business, 'name', 'Business'),
        "influencer_name": getattr(influencer, 'name', 'Influencer'),
        "campaign_title": request.campaign_title,
        "estimated_completion": "30-60 seconds",
        "check_status_url": f"/documents/{new_doc.id}/status",
        "download_url": f"/documents/{new_doc.id}/download"
    }


@router.post("/generate-collaboration-request-general", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_general_collaboration_request_async(
    request: GeneralCollaborationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a general collaboration request for multiple influencers"""
    
    # Validate business exists
    business_result = await db.execute(
        select(Business).where(Business.id == request.business_id)
    )
    business = await safe_scalar_one_or_none(business_result)
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Create job record
    job_id = str(uuid.uuid4())
    
    new_doc = GeneratedDocumentModel(
        user_id=getattr(business, 'user_id', 1),
        template_id=None,
        type='collaboration_request',
        subtype='general_outreach',
        business_id=request.business_id,
        parameters={
            'campaign_title': request.campaign_title,
            'campaign_description': request.campaign_description,
            'target_audience': request.target_audience,
            'target_follower_range': request.target_follower_range,
            'preferred_niches': request.preferred_niches,
            'deliverables': request.deliverables,
            'compensation_range': request.compensation_range,
            'campaign_duration': request.campaign_duration,
            'content_requirements': request.content_requirements,
            'brand_guidelines': request.brand_guidelines,
            'deadline': request.deadline,
            'target_countries': request.target_countries,
            'file_format': request.file_format
        },
        file_path=f"pending_{job_id}",
        generation_status='pending',
        created_at=func.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Add background task
    background_tasks.add_task(
        generate_general_collaboration_background,
        new_doc.id,
        request
    )
    
    logger.info(f"Started general collaboration request generation for document ID: {new_doc.id}")
    
    return {
        "message": "General collaboration request generation started",
        "job_id": job_id,
        "document_id": new_doc.id,
        "status": "pending",
        "business_name": getattr(business, 'name', 'Business'),
        "campaign_title": request.campaign_title,
        "target_niches": request.preferred_niches,
        "estimated_completion": "30-60 seconds",
        "check_status_url": f"/documents/{new_doc.id}/status",
        "download_url": f"/documents/{new_doc.id}/download"
    }


@router.post("/generate-collaboration-request-public", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def generate_public_collaboration_request_async(
    data: PublicCollaborationRequest,  # ✅ Renamed from 'request' to avoid conflict
    request: Request,  # ✅ Move Request parameter before Depends()
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a general collaboration request for multiple influencers without authentication"""
    
    # Enhanced monitoring - Log request details
    client_ip = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    business_name = data.business_profile.get('name', 'Unknown Business')  # ✅ Use 'data' instead of 'request'
    
    logger.info(f"Public document request from IP: {client_ip}")
    logger.info(f"User-Agent: {user_agent}")
    logger.info(f"Business: {business_name}")
    logger.info(f"Campaign: {data.campaign_title}")  # ✅ Use 'data'
    
    # Create job record
    job_id = str(uuid.uuid4())
    
    new_doc = GeneratedDocumentModel(
        user_id=1,  # Default user ID for public requests
        template_id=None,
        type='collaboration_request',
        subtype='public_outreach',
        business_id=None,  # No business ID since this is public
        parameters={
            'business_profile': data.business_profile,  # ✅ Use 'data'
            'campaign_title': data.campaign_title,  # ✅ Use 'data'
            'campaign_description': data.campaign_description,  # ✅ Use 'data'
            'target_audience': data.target_audience,  # ✅ Use 'data'
            'target_follower_range': data.target_follower_range,  # ✅ Use 'data'
            'preferred_niches': data.preferred_niches,  # ✅ Use 'data'
            'deliverables': data.deliverables,  # ✅ Use 'data'
            'compensation_range': data.compensation_range,  # ✅ Use 'data'
            'campaign_duration': data.campaign_duration,  # ✅ Use 'data'
            'content_requirements': data.content_requirements,  # ✅ Use 'data'
            'brand_guidelines': data.brand_guidelines,  # ✅ Use 'data'
            'deadline': data.deadline,  # ✅ Use 'data'
            'target_countries': data.target_countries,  # ✅ Use 'data'
            'file_format': data.file_format,  # ✅ Use 'data'
            'client_ip': client_ip,  # Store client IP for monitoring
            'user_agent': user_agent  # Store user agent for monitoring
        },
        file_path=f"pending_{job_id}",
        generation_status='pending',
        created_at=func.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Add background task
    background_tasks.add_task(
        generate_public_collaboration_background,
        new_doc.id,
        data  # ✅ Pass 'data' to background task
    )
    
    logger.info(f"Started public collaboration request generation for document ID: {new_doc.id} from IP: {client_ip}")
    
    return {
        "message": "Public collaboration request generation started",
        "job_id": job_id,
        "document_id": new_doc.id,
        "status": "pending",
        "business_name": data.business_profile.get('name', 'Business'),  # ✅ Use 'data'
        "campaign_title": data.campaign_title,  # ✅ Use 'data'
        "target_niches": data.preferred_niches,  # ✅ Use 'data'
        "estimated_completion": "30-60 seconds",
        "check_status_url": f"/documents/{new_doc.id}/status",
        "download_url": f"/documents/{new_doc.id}/download"
    }


@router.post("/generate-market-analysis-public", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def generate_public_market_analysis_async(
    data: MarketAnalysisRequest,  # ✅ Only business profile data
    request: Request,  # ✅ Move Request parameter before Depends()
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate country-by-country market analysis without authentication"""
    
    # Enhanced monitoring - Log request details
    client_ip = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    business_name = data.business_profile.get('name', 'Unknown Business')
    
    logger.info(f"Public market analysis request from IP: {client_ip}")
    logger.info(f"User-Agent: {user_agent}")
    logger.info(f"Business: {business_name}")
    
    # Create job record
    job_id = str(uuid.uuid4())
    
    new_doc = GeneratedDocumentModel(
        user_id=1,  # Default user ID for public requests
        template_id=None,
        type='market_analysis',
        subtype='country_analysis',
        business_id=None,  # No business ID since this is public
        parameters={
            'business_profile': data.business_profile,
            'client_ip': client_ip,  # Store client IP for monitoring
            'user_agent': user_agent  # Store user agent for monitoring
        },
        file_path=f"pending_{job_id}",
        generation_status='pending',
        created_at=func.now()
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Add background task
    background_tasks.add_task(
        generate_public_market_analysis_background,
        new_doc.id,
        data
    )
    
    logger.info(f"Started public market analysis generation for document ID: {new_doc.id} from IP: {client_ip}")
    
    return {
        "message": "Public market analysis generation started",
        "job_id": job_id,
        "document_id": new_doc.id,
        "status": "pending",
        "business_name": data.business_profile.get('name', 'Business'),
        "estimated_completion": "30-60 seconds",
        "check_status_url": f"/documents/{new_doc.id}/status",
        "download_url": f"/documents/{new_doc.id}/download"
    }


@router.post("/generate-social-media-plan-public", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def generate_public_social_media_plan_async(
    data: SocialMediaPlanRequest,  # ✅ Only influencer profile data
    request: Request,  # ✅ Move Request parameter before Depends()
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a comprehensive 1-month social media plan for an influencer"""
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create document record
        new_doc = GeneratedDocumentModel(
            user_id=1,  # Default user ID for public requests
            template_id=None,
            type='social_media_plan',
            subtype='monthly_plan',
            business_id=None,  # No business ID since this is public
            parameters=data.dict(),
            file_path=f"pending_{job_id}",  # ✅ Add temporary file path
            generation_status='pending',
            created_at=func.now(),
            updated_at=func.now()
        )
        
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        document_id = new_doc.id
        logger.info(f"Public social media plan generation started (ID: {document_id})")
        
        # Add background task
        background_tasks.add_task(
            generate_public_social_media_plan_background,
            document_id,
            data
        )
        
        return {
            "message": "Social media plan generation started",
            "job_id": job_id,
            "document_id": document_id,
            "status": "pending",
            "estimated_completion": "30-60 seconds",
            "check_status_url": f"/documents/{document_id}/status",
            "download_url": f"/documents/{document_id}/download"
        }
        
    except Exception as e:
        logger.error(f"Failed to start public social media plan generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start social media plan generation")


@router.post("/generate-business-plan-public", response_model=Dict, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def generate_public_business_plan_async(
    data: InfluencerBusinessPlanRequest,  # ✅ Only influencer profile data
    request: Request,  # ✅ Move Request parameter before Depends()
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a comprehensive business plan for an influencer"""
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create document record
        new_doc = GeneratedDocumentModel(
            user_id=1,  # Default user ID for public requests
            template_id=None,
            type='business_plan',
            subtype='influencer_plan',
            business_id=None,  # No business ID since this is public
            parameters=data.dict(),
            file_path=f"pending_{job_id}",  # ✅ Add temporary file path
            generation_status='pending',
            created_at=func.now(),
            updated_at=func.now()
        )
        
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        document_id = new_doc.id
        logger.info(f"Public business plan generation started (ID: {document_id})")
        
        # Add background task
        background_tasks.add_task(
            generate_public_business_plan_background,
            document_id,
            data
        )
        
        return {
            "message": "Business plan generation started",
            "job_id": job_id,
            "document_id": document_id,
            "status": "pending",
            "estimated_completion": "30-60 seconds",
            "check_status_url": f"/documents/{document_id}/status",
            "download_url": f"/documents/{document_id}/download"
        }
        
    except Exception as e:
        logger.error(f"Failed to start public business plan generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start business plan generation")


async def generate_specific_collaboration_background(
    document_id: int,
    request: SpecificCollaborationRequest
):
    """Background task for specific influencer collaboration request generation"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to processing
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            # Fetch business and influencer details
            business_result = await db.execute(
                select(Business).where(Business.id == request.business_id)
            )
            business = business_result.scalar_one()
            
            influencer_result = await db.execute(
                select(Influencer).where(Influencer.id == request.influencer_id)
            )
            influencer = influencer_result.scalar_one()
            
            # Create comprehensive specific collaboration prompt
            deliverables_text = "\n".join([f"- {item}" for item in request.deliverables])
            
            collaboration_prompt = f"""
# Personalized Collaboration Request

# Business Information
**Company:** {getattr(business, 'name', 'Our Company')}
**Description:** {getattr(business, 'description', 'Leading brand in our industry')}
**Industry:** {getattr(business, 'industry', 'Various')}
**Website:** {getattr(business, 'website', 'www.company.com')}

# Influencer Profile
**Name:** {getattr(influencer, 'name', 'Valued Creator')}
**Username:** @{getattr(influencer, 'username', 'creator')}
**Bio:** {getattr(influencer, 'bio', 'Content creator and influencer')}
**Followers:** {getattr(influencer, 'follower_count', 'N/A')}
**Niche:** {getattr(influencer, 'niche', 'General')}
**Location:** {getattr(influencer, 'location', 'Global')}

# Campaign Proposal: {request.campaign_title}

## Campaign Overview
{request.campaign_description}

## Why We Chose You
Based on your profile and content style, we believe you're the perfect fit for this campaign because:
- Your audience aligns perfectly with our target demographic
- Your content quality and engagement rates are impressive
- Your personal brand values match our company values

## Campaign Requirements
**Duration:** {request.campaign_duration}
**Deadline:** {request.deadline}

## Deliverables
{deliverables_text}

## Content Requirements
{request.content_requirements}

## Brand Guidelines
{request.brand_guidelines if request.brand_guidelines else 'We will provide detailed brand guidelines upon agreement'}

## Compensation
**Offered Amount:** ${request.compensation_amount:,.2f}
**Payment Terms:** 50% upfront, 50% upon completion
**Additional Benefits:** Product samples, long-term partnership opportunities

## Success Metrics
We'll track the following KPIs:
- Reach and impressions
- Engagement rate (likes, comments, shares)
- Click-through rate to our website
- Conversion rate and sales attribution

## Next Steps
1. Review this collaboration proposal
2. Schedule a brief call to discuss details
3. Sign collaboration agreement
4. Receive campaign brief and assets
5. Begin content creation

## Contact Information
**Project Manager:** [Name]
**Email:** partnerships@company.com
**Phone:** [Phone Number]

We're excited about the possibility of working together and believe this partnership will be mutually beneficial. Please let us know if you have any questions or would like to discuss any aspects of this proposal.

Generate a professional, personalized collaboration request document based on this information.
"""

            # Create template object
            template = SimpleNamespace(
                id='specific_collaboration_template',
                prompt_text=collaboration_prompt,
                file_format=request.file_format,
                type='collaboration_request',
                subtype='specific_influencer'
            )
            
            # Parameters and related data
            parameters = {
                'business_name': getattr(business, 'name', 'Company'),
                'influencer_name': getattr(influencer, 'name', 'Creator'),
                'campaign_title': request.campaign_title,
                'compensation_amount': request.compensation_amount,
                'file_format': request.file_format
            }
            
            related_data = {
                'business_id': request.business_id,
                'influencer_id': request.influencer_id,
                'user_id': getattr(business, 'user_id', None)
            }
            
            # Generate document
            business_name = getattr(business, 'name', f'Business {request.business_id}')
            influencer_name = getattr(influencer, 'name', f'Influencer {request.influencer_id}')
            logger.info(f"Generating specific collaboration request '{request.campaign_title}' for business '{business_name}' (ID: {request.business_id}) → influencer '{influencer_name}' (ID: {request.influencer_id})")
            file_path = generate_document(template, parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            doc.parameters = parameters
            
            await db.commit()
            logger.info(f"Specific collaboration request '{request.campaign_title}' (ID: {document_id}) generated successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"Specific collaboration request generation failed for document ID {document_id}: {e}")
            
            try:
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update error status for document {document_id}: {db_error}")


async def generate_general_collaboration_background(
    document_id: int,
    request: GeneralCollaborationRequest
):
    """Background task for general collaboration request generation"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to processing
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            # Fetch business details
            business_result = await db.execute(
                select(Business).where(Business.id == request.business_id)
            )
            business = business_result.scalar_one()
            
            # Create comprehensive general collaboration prompt
            deliverables_text = "\n".join([f"- {item}" for item in request.deliverables])
            niches_text = ", ".join(request.preferred_niches)
            countries_text = ", ".join(request.target_countries)
            
            collaboration_prompt = f"""
# General Collaboration Opportunity

# About Our Company
**Company:** {getattr(business, 'name', 'Our Company')}
**Description:** {getattr(business, 'description', 'Leading brand in our industry')}
**Industry:** {getattr(business, 'industry', 'Various')}
**Website:** {getattr(business, 'website', 'www.company.com')}
**Mission:** Creating authentic connections between brands and creators

# Campaign: {request.campaign_title}

## Campaign Overview
{request.campaign_description}

## Who We're Looking For
**Target Audience:** {request.target_audience}
**Follower Range:** {request.target_follower_range}
**Preferred Niches:** {niches_text}
**Location:** {countries_text}

## What Makes You Perfect
We're seeking creators who:
- Have authentic engagement with their audience
- Create high-quality, original content
- Align with our brand values of authenticity and creativity
- Are professional and reliable in their collaborations

## Campaign Details
**Duration:** {request.campaign_duration}
**Deadline:** {request.deadline}

## Deliverables Required
{deliverables_text}

## Content Guidelines
{request.content_requirements}

## Brand Standards
{request.brand_guidelines if request.brand_guidelines else 'Detailed brand guidelines will be provided to selected creators'}

## Compensation Package
**Range:** {request.compensation_range}
**Payment Structure:** 
- 50% upon agreement signing
- 50% upon campaign completion and approval

**Additional Benefits:**
- Product samples and exclusive access
- Performance bonuses for exceptional results
- Opportunity for long-term partnership
- Featured placement in our creator network

## Success Metrics & KPIs
We measure success through:
- **Reach:** Total audience reached across all content
- **Engagement:** Average engagement rate of 3%+ target
- **Brand Awareness:** Increase in brand mention and recognition
- **Traffic:** Click-through rate to our website/landing pages
- **Conversions:** Sales attributed to influencer content

## Application Process
**How to Apply:**
1. Review this collaboration opportunity
2. Submit your media kit and recent analytics
3. Provide 3 examples of similar brand collaborations
4. Schedule a brief introductory call

**Selection Criteria:**
- Content quality and brand alignment
- Audience demographics match
- Professional communication and reliability
- Creative ideas and unique approach

## Timeline
- **Applications Close:** [Date]
- **Creator Selection:** Within 5 business days
- **Campaign Brief:** Sent to selected creators
- **Content Creation Period:** {request.campaign_duration}
- **Final Review & Payment:** Within 5 days of completion

## Frequently Asked Questions

**Q: Can I apply if I'm slightly outside the follower range?**
A: Yes! We value engagement quality over follower count.

**Q: Do you provide content briefs?**
A: Absolutely! Selected creators receive detailed briefs and assets.

**Q: Is this a one-time collaboration?**
A: We're looking for both one-time and ongoing partnerships.

## Contact & Next Steps
**Partnership Team:** partnerships@company.com
**Application Portal:** [URL]
**Questions:** influencer-support@company.com

We're excited to work with creative, authentic influencers who can help us reach new audiences in meaningful ways. This is an opportunity to partner with a growing brand that values long-term creator relationships.

Generate a professional, comprehensive general collaboration request document based on this information.
"""

            # Create template object
            template = SimpleNamespace(
                id='general_collaboration_template',
                prompt_text=collaboration_prompt,
                file_format=request.file_format,
                type='collaboration_request',
                subtype='general_outreach'
            )
            
            # Parameters and related data
            parameters = {
                'business_name': getattr(business, 'name', 'Company'),
                'campaign_title': request.campaign_title,
                'target_niches': niches_text,
                'compensation_range': request.compensation_range,
                'file_format': request.file_format
            }
            
            related_data = {
                'business_id': request.business_id,
                'user_id': getattr(business, 'user_id', None)
            }
            
            # Generate document
            business_name = getattr(business, 'name', f'Business {request.business_id}')
            logger.info(f"Generating general collaboration request '{request.campaign_title}' for business '{business_name}' (ID: {request.business_id})")
            file_path = generate_document(template, parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            doc.parameters = parameters
            
            await db.commit()
            logger.info(f"General collaboration request '{request.campaign_title}' (ID: {document_id}) generated successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"General collaboration request generation failed for document ID {document_id}: {e}")
            
            try:
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update error status for document {document_id}: {db_error}")


async def generate_public_collaboration_background(
    document_id: int,
    request: PublicCollaborationRequest
):
    """Background task for public collaboration request generation"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to processing
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            # Create comprehensive public collaboration prompt
            business_profile_text = "\n".join([f"- {k}: {v}" for k, v in request.business_profile.items()])
            niches_text = ", ".join(request.preferred_niches)
            countries_text = ", ".join(request.target_countries)
            
            collaboration_prompt = f"""
# Public Collaboration Opportunity

# About Our Company
**Company:** {request.business_profile.get('name', 'Our Company')}
**Description:** {request.business_profile.get('description', 'Leading brand in our industry')}
**Industry:** {request.business_profile.get('industry', 'Various')}
**Website:** {request.business_profile.get('website', 'www.company.com')}
**Mission:** Creating authentic connections between brands and creators

# Campaign: {request.campaign_title}

## Campaign Overview
{request.campaign_description}

## Who We're Looking For
**Target Audience:** {request.target_audience}
**Follower Range:** {request.target_follower_range}
**Preferred Niches:** {niches_text}
**Location:** {countries_text}

## What Makes You Perfect
We're seeking creators who:
- Have authentic engagement with their audience
- Create high-quality, original content
- Align with our brand values of authenticity and creativity
- Are professional and reliable in their collaborations

## Campaign Details
**Duration:** {request.campaign_duration}
**Deadline:** {request.deadline}

## Deliverables Required
{request.deliverables}

## Content Guidelines
{request.content_requirements}

## Brand Standards
{request.brand_guidelines if request.brand_guidelines else 'Detailed brand guidelines will be provided to selected creators'}

## Compensation Package
**Range:** {request.compensation_range}
**Payment Structure:** 
- 50% upon agreement signing
- 50% upon campaign completion and approval

**Additional Benefits:**
- Product samples and exclusive access
- Performance bonuses for exceptional results
- Opportunity for long-term partnership
- Featured placement in our creator network

## Success Metrics & KPIs
We measure success through:
- **Reach:** Total audience reached across all content
- **Engagement:** Average engagement rate of 3%+ target
- **Brand Awareness:** Increase in brand mention and recognition
- **Traffic:** Click-through rate to our website/landing pages
- **Conversions:** Sales attributed to influencer content

## Application Process
**How to Apply:**
1. Review this collaboration opportunity
2. Submit your media kit and recent analytics
3. Provide 3 examples of similar brand collaborations
4. Schedule a brief introductory call

**Selection Criteria:**
- Content quality and brand alignment
- Audience demographics match
- Professional communication and reliability
- Creative ideas and unique approach

## Timeline
- **Applications Close:** [Date]
- **Creator Selection:** Within 5 business days
- **Campaign Brief:** Sent to selected creators
- **Content Creation Period:** {request.campaign_duration}
- **Final Review & Payment:** Within 5 days of completion

## Frequently Asked Questions

**Q: Can I apply if I'm slightly outside the follower range?**
A: Yes! We value engagement quality over follower count.

**Q: Do you provide content briefs?**
A: Absolutely! Selected creators receive detailed briefs and assets.

**Q: Is this a one-time collaboration?**
A: We're looking for both one-time and ongoing partnerships.

## Contact & Next Steps
**Partnership Team:** partnerships@company.com
**Application Portal:** [URL]
**Questions:** influencer-support@company.com

We're excited to work with creative, authentic influencers who can help us reach new audiences in meaningful ways. This is an opportunity to partner with a growing brand that values long-term creator relationships.

Generate a professional, comprehensive general collaboration request document based on this information.
"""

            # Create template object
            template = SimpleNamespace(
                id='public_collaboration_template',
                prompt_text=collaboration_prompt,
                file_format=request.file_format,
                type='collaboration_request',
                subtype='public_outreach'
            )
            
            # Parameters and related data
            parameters = {
                'business_name': request.business_profile.get('name', 'Company'),
                'campaign_title': request.campaign_title,
                'target_niches': niches_text,
                'compensation_range': request.compensation_range,
                'file_format': request.file_format
            }
            
            related_data = {
                'user_id': 1 # Default user ID for public requests
            }
            
            # Generate document
            business_name = request.business_profile.get('name', f'Business {request.business_profile.get("id", "N/A")}')
            logger.info(f"Generating public collaboration request '{request.campaign_title}' for business '{business_name}' (ID: {request.business_profile.get('id', 'N/A')})")
            file_path = generate_document(template, parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            doc.parameters = parameters
            
            await db.commit()
            logger.info(f"Public collaboration request '{request.campaign_title}' (ID: {document_id}) generated successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"Public collaboration request generation failed for document ID {document_id}: {e}")
            
            try:
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update error status for document {document_id}: {db_error}")


async def generate_public_market_analysis_background(
    document_id: int,
    request: MarketAnalysisRequest
):
    """Background task for public market analysis generation"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to processing
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            # Get country names from collaboration_country_ids
            collaboration_country_ids = request.business_profile.get('collaboration_country_ids', [])
            country_names = []
            
            if collaboration_country_ids:
                # Query countries from database
                from app.db.models.country import Country
                countries_result = await db.execute(
                    select(CountryModel).where(CountryModel.id.in_(collaboration_country_ids))
                )
                countries = countries_result.scalars().all()
                country_names = [country.name for country in countries]
            
            # Fallback to target_countries if no collaboration countries found
            if not country_names:
                country_names = request.business_profile.get('target_countries', ['United States'])
            
            countries_text = ", ".join(country_names)
            
            # Create comprehensive country-by-country market analysis prompt
            business_name = request.business_profile.get('name', 'Our Company')
            business_description = request.business_profile.get('description', 'Leading brand in our industry')
            business_industry = request.business_profile.get('industry', 'Various')
            business_website = request.business_profile.get('website_url', 'www.company.com')
            base_country_id = request.business_profile.get('base_country_id')
            
            # Get base country name if available
            base_country_name = "Global"
            if base_country_id:
                base_country_result = await db.execute(
                    select(CountryModel).where(CountryModel.id == base_country_id)
                )
                base_country = await safe_scalar_one_or_none(base_country_result)
                if base_country:
                    base_country_name = base_country.name
            
            market_analysis_prompt = f"""
# Comprehensive Market Analysis Report
## {business_name} - Global Market Opportunity Assessment

### Executive Summary
{business_name} is a {business_industry} company based in {base_country_name}, seeking to expand its market presence through strategic influencer partnerships across multiple countries. This report provides a detailed country-by-country market analysis to support informed decision-making for international expansion.

### Company Profile
- **Company Name:** {business_name}
- **Industry:** {business_industry}
- **Description:** {business_description}
- **Website:** {business_website}
- **Base Country:** {base_country_name}
- **Target Markets:** {countries_text}

### Methodology
This analysis examines market opportunities, competitive landscapes, influencer ecosystems, and entry strategies for each target country. The assessment considers cultural factors (very important), customer preference ( extremely important) regulatory environments (important), market maturity (important), and digital adoption rates (important).

### Country-by-Country Market Analysis

"""
            
            # Add dynamic country-specific sections
            for i, country_name in enumerate(country_names, 1):
                market_analysis_prompt += f"""
## {i}. {country_name} Market Analysis

### Market Overview
- **Market Size:** [Provide estimated market size for {business_industry} in {country_name}]
- **Growth Rate:** [Annual growth rate and trends with data]
- **Market Maturity:** [Early-stage, growing, or mature market with data]
- **Digital Adoption:** [Social media penetration and influencer marketing maturity with data]

### Competitive Landscape
- **Key Players:** [Major competitors in {country_name} for {business_industry}]
- **Market Share Distribution:** [How the market is divided among competitors with data]
- **Competitive Advantages:** [What makes {business_name} unique in this market with data]
- **Barriers to Entry:** [Regulatory, cultural, or economic barriers with data]

### Target Demographics
- **Primary Audience:** [Age groups, income levels, interests relevant to {business_industry} with data]
- **Social Media Usage:** [Popular platforms and usage patterns in {country_name} with data]
- **Content Preferences:** [Types of content that resonate with local audiences with data]
- **Cultural Considerations:** [Local customs, values, and communication styles with data]
- **Language:** [Local language and translation requirements with data]
- **Language barriers:** [Language barriers and translation requirements with data]
- **Currency & Foreign Exchange Restrictions:** [Currency restrictions and exchange rates compared to the US Dollars with data]

### Influencer Ecosystem
- **Influencer Categories:** [Micro, macro, and mega influencers in {country_name} with data]
- **Platform Preferences:** [Most popular social media platforms for influencer marketing with data]
- **Engagement Rates:** [Typical engagement rates by influencer tier with data]
- **Compensation Ranges:** [Average rates for different influencer tiers with data]
- **Content Types:** [Most effective content formats for {country_name} with data]

### Market Opportunities
- **Untapped Segments:** [Underserved audience segments in {country_name} with data]
- **Emerging Trends:** [New trends in {business_industry} specific to {country_name} with data]
- **Partnership Opportunities:** [Potential local partners or collaborators with data]
- **Growth Drivers:** [Factors driving market growth in {country_name} with data]

### Challenges and Risks
- **Regulatory Environment:** [Local regulations affecting {business_industry} with data]
- **Cultural Barriers:** [Potential cultural misunderstandings or resistance with data]
- **Economic Factors:** [Currency fluctuations, economic stability with data]
- **Competition Intensity:** [Level of competition and market saturation with data]

### Entry Strategy Recommendations
- **Timeline:** [Recommended entry timeline for {country_name} with data and timeline]
- **Approach:** [Gradual vs. aggressive market entry strategy with data]
- **Partnership Strategy:** [Local partnerships and collaborations with data]
- **Content Localization:** [Adaptation strategies for local audiences with data]
- **Budget Allocation:** [Recommended investment levels for {country_name} with data]

### Success Metrics
- **KPIs:** [Key performance indicators for {country_name} market with data]
- **ROI Expectations:** [Expected return on investment timeline with data]
- **Growth Targets:** [Realistic growth targets for first 12 months with data]
- **Market Share Goals:** [Target market share in {country_name} with data]

### Case Studies and Examples
- **Success Stories:** [Examples of similar companies succeeding in {country_name} with data]
- **Failure Lessons:** [Common mistakes to avoid in {country_name} with data]
- **Best Practices:** [Proven strategies for {business_industry} in {country_name} with data]

"""

            # Add comprehensive conclusion and recommendations
            market_analysis_prompt += f"""

#### Resource Allocation Strategy
- **Primary Market Investment:** [Recommended budget allocation for top priority market with data]
- **Secondary Market Testing:** [Pilot program recommendations for other markets with data]
- **Shared Resources:** [Common resources that can be leveraged across markets with data]

#### Risk Mitigation
- **Diversification Strategy:** [How to spread risk across multiple markets with data]
- **Exit Strategies:** [Plans for scaling back if markets don't perform with data]
- **Contingency Plans:** [Backup strategies for unexpected challenges with data]

### Strategic Recommendations

#### Short-term (3-6 months)
1. **[Immediate Action 1]:** [Specific action with timeline with data]
2. **[Immediate Action 2]:** [Specific action with timeline with data]
3. **[Immediate Action 3]:** [Specific action with timeline with data]

#### Medium-term (6-12 months)
1. **[Strategic Initiative 1]:** [Market expansion or partnership development with data]
2. **[Strategic Initiative 2]:** [Product or service adaptation with data]
3. **[Strategic Initiative 3]:** [Team building and local presence with data]

#### Long-term (12+ months)
1. **[Long-term Goal 1]:** [Market leadership or significant market share]
2. **[Long-term Goal 2]:** [Regional expansion or new market entry]
3. **[Long-term Goal 3]:** [Brand establishment and market dominance]

### Implementation Roadmap

#### Phase 1: Market Entry Preparation (Months 1-3)
- [Detailed tasks for market research and preparation with data]
- [Local team hiring and training with data]
- [Partnership development with data]
- [Content localization planning with data]

#### Phase 2: Market Launch (Months 4-6)
- [Influencer partnership activation with data]
- [Content campaign launch with data]
- [Performance monitoring setup with data]
- [Customer feedback collection with data]

#### Phase 3: Market Expansion (Months 7-12)
- [Scale successful campaigns with data]
- [Expand influencer network with data]
- [Optimize based on performance data]
- [Prepare for additional market entry with data]

### Financial Projections

#### Investment Requirements
- **Initial Investment:** [Total investment needed for market entry with data]
- **Monthly Operating Costs:** [Ongoing costs for market presence with data]
- **ROI Timeline:** [Expected time to break even and generate profit with data]

#### Revenue Projections
- **Year 1 Revenue:** [Conservative, realistic, and optimistic projections with data]
- **Year 2 Growth:** [Expected growth rates and market expansion with data]
- **Year 3 Scaling:** [Long-term revenue and market share goals with data]


### Contact Information

**Report Prepared For:** {business_name}
**Analysis Date:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
**Target Markets:** {countries_text}
**Base Country:** {base_country_name}
**Contact Email:** {request.business_profile.get('contact_email', 'Not provided')}
**Contact Phone:** {request.business_profile.get('contact_phone', 'Not provided')}

### Conclusion

This comprehensive market analysis provides {business_name} with a strategic roadmap for international expansion through influencer partnerships. The country-by-country analysis reveals unique opportunities and challenges in each market, enabling informed decision-making and resource allocation.

The recommended approach focuses on [key strategic elements], with particular emphasis on [specific market opportunities]. Success in these markets will establish {business_name} as a [desired market position] and create a foundation for further international expansion.

Generate a professional, comprehensive market analysis document based on this detailed framework. Ensure each country section contains specific, actionable insights and realistic projections based on the provided business profile and market characteristics. Ensure you do not miss any sections or details. And all section are pupulated with examples and data.
"""

            logger.info(f"Market analysis prompt: {market_analysis_prompt}")

            # Create template object
            template = SimpleNamespace(
                id='market_analysis_template',
                prompt_text=market_analysis_prompt,
                file_format=request.business_profile.get('file_format', 'pdf'),  # ✅ Extract from business_profile
                type='market_analysis',
                subtype='country_analysis'
            )
            
            # Parameters and related data
            parameters = {
                'business_name': request.business_profile.get('name', 'Company'),
                'target_countries': countries_text,
                'file_format': request.business_profile.get('file_format', 'pdf')  # ✅ Extract from business_profile
            }
            
            related_data = {
                'user_id': 1 # Default user ID for public requests
            }
            
            # Generate document
            business_name = request.business_profile.get('name', f'Business {request.business_profile.get("id", "N/A")}')
            logger.info(f"Generating public market analysis for business '{business_name}' (ID: {request.business_profile.get('id', 'N/A')}) targeting {countries_text}")
            file_path = generate_document(template, parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            doc.parameters = parameters
            
            await db.commit()
            logger.info(f"Public market analysis '{countries_text}' (ID: {document_id}) generated successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"Public market analysis generation failed for document ID {document_id}: {e}")
            
            try:
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update error status for document {document_id}: {db_error}")


async def generate_public_social_media_plan_background(
    document_id: int,
    request: SocialMediaPlanRequest
):
    """Background task to generate social media plan document"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to processing
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            # Extract influencer profile data
            influencer_profile = request.influencer_profile
            
            # Get influencer details
            first_name = influencer_profile.get('first_name', 'Anonymous')
            last_name = influencer_profile.get('last_name', 'User')
            full_name = f"{first_name} {last_name}".strip()
            email = influencer_profile.get('email', 'Not provided')
            bio = influencer_profile.get('bio', 'No bio provided')
            website_url = influencer_profile.get('website_url', '')
            languages = influencer_profile.get('languages', 'English')
            base_country_id = influencer_profile.get('base_country_id', 1)
            content_type = influencer_profile.get('content_type', 'General Content')
            base_rate = influencer_profile.get('base_rate', 0)
            
            # Get country information
            country_result = await db.execute(
                select(CountryModel).where(CountryModel.id == base_country_id)
            )
            country = await safe_scalar_one_or_none(country_result)
            country_name = country.name if country else "Unknown"
            
            # Create comprehensive social media plan prompt
            social_media_plan_prompt = f"""
You are a professional social media strategist creating a comprehensive 1-month social media plan for an influencer. 

## Influencer Profile:
**Name:** {full_name}
**Email:** {email}
**Bio:** {bio}
**Website:** {website_url}
**Languages:** {languages}
**Base Country:** {country_name}
**Content Type:** {content_type}
**Base Rate:** ${base_rate}

## Task:
Create a detailed 1-month social media plan that includes:

### 1. Content Strategy (Week 1-4)
- **Content Themes:** Define 4 main themes for the month
- **Content Mix:** 60% educational/value, 25% entertaining, 15% promotional
- **Posting Schedule:** Optimal times for each platform
- **Content Pillars:** 3-4 main content categories

### 2. Weekly Breakdown
**Week 1:**
- Content focus and goals
- Specific post ideas (3-5 per platform)
- Hashtag strategy
- Engagement tactics

**Week 2:**
- Content focus and goals
- Specific post ideas (3-5 per platform)
- Cross-platform content adaptation
- Collaboration opportunities

**Week 3:**
- Content focus and goals
- Specific post ideas (3-5 per platform)
- Trend integration
- Audience growth strategies

**Week 4:**
- Content focus and goals
- Specific post ideas (3-5 per platform)
- Monthly review preparation
- Next month planning

### 3. Platform-Specific Strategy
- **Instagram:** Stories, Reels, Posts, IGTV
- **TikTok:** Trending sounds, challenges, duets
- **YouTube:** Video ideas, thumbnails, descriptions
- **Twitter:** Thread ideas, engagement tactics
- **LinkedIn:** Professional content, networking

### 4. Growth & Engagement Strategy
- **Follower Growth Goals:** Realistic monthly targets
- **Engagement Rate Improvement:** Tactics and metrics
- **Collaboration Strategy:** Brand partnerships, influencer collaborations
- **Community Building:** Audience interaction tactics

### 5. Analytics & Optimization
- **Key Metrics to Track:** Engagement rate, reach, saves, shares
- **Weekly Review Schedule:** What to analyze and adjust
- **A/B Testing Ideas:** Content variations to test
- **Performance Optimization:** Based on analytics

### 6. Monetization Strategy
- **Brand Partnership Opportunities:** Based on content type and rate
- **Affiliate Marketing:** Product recommendations
- **Sponsored Content:** Integration strategies
- **Revenue Diversification:** Multiple income streams

### 7. Tools & Resources
- **Content Creation Tools:** Apps and software recommendations
- **Analytics Tools:** Tracking and measurement
- **Scheduling Tools:** Post management
- **Design Resources:** Templates and assets

### 8. Monthly Goals & KPIs
- **Follower Growth Target:** Realistic monthly increase
- **Engagement Rate Target:** Percentage improvement
- **Content Output:** Number of posts per platform
- **Revenue Goals:** Income targets and strategies

### 9. Risk Management
- **Content Backup Plans:** Alternative content ideas
- **Crisis Management:** How to handle negative feedback
- **Platform Changes:** Adapting to algorithm updates
- **Trend Monitoring:** Staying relevant

### 10. Success Metrics
- **Quantitative Goals:** Numbers and percentages
- **Qualitative Goals:** Brand perception, audience sentiment
- **Monthly Review Template:** What to evaluate
- **Adjustment Strategies:** How to pivot based on performance

Generate a professional, comprehensive 1-month social media plan based on this detailed framework. Ensure each section contains specific, actionable insights and realistic strategies based on the provided influencer profile. Include practical examples, specific post ideas, and measurable goals. Make the plan highly personalized to the influencer's content type, rate, and target audience.
"""

            logger.info(f"Social media plan prompt: {social_media_plan_prompt}")

            # Create template object
            template = SimpleNamespace(
                id='social_media_plan_template',
                prompt_text=social_media_plan_prompt,
                file_format=request.file_format,
                type='social_media_plan',
                subtype='monthly_plan'
            )
            
            # Parameters and related data
            parameters = {
                'influencer_name': full_name,
                'content_type': content_type,
                'base_rate': base_rate,
                'country': country_name,
                'file_format': request.file_format
            }
            
            related_data = {
                'user_id': 1 # Default user ID for public requests
            }
            
            # Generate document
            logger.info(f"Generating public social media plan for influencer '{full_name}' (ID: {document_id})")
            file_path = generate_document(template, parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            doc.parameters = parameters
            
            await db.commit()
            logger.info(f"Public social media plan (ID: {document_id}) generated successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"Public social media plan generation failed for document ID {document_id}: {e}")
            
            try:
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update error status for document {document_id}: {db_error}")


async def generate_public_business_plan_background(
    document_id: int,
    request: InfluencerBusinessPlanRequest
):
    """Background task to generate business plan document"""
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        try:
            # Update status to processing
            doc_result = await db.execute(
                select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one()
            
            doc.generation_status = 'processing'
            doc.updated_at = func.now()
            await db.commit()
            
            # Extract influencer profile data
            influencer_profile = request.influencer_profile
            
            # Get influencer details
            first_name = influencer_profile.get('first_name', 'Anonymous')
            last_name = influencer_profile.get('last_name', 'User')
            full_name = f"{first_name} {last_name}".strip()
            email = influencer_profile.get('email', 'Not provided')
            bio = influencer_profile.get('bio', 'No bio provided')
            website_url = influencer_profile.get('website_url', '')
            languages = influencer_profile.get('languages', 'English')
            base_country_id = influencer_profile.get('base_country_id', 1)
            content_type = influencer_profile.get('content_type', 'General Content')
            base_rate = influencer_profile.get('base_rate', 0)
            
            # Get country information
            country_result = await db.execute(
                select(CountryModel).where(CountryModel.id == base_country_id)
            )
            country = await safe_scalar_one_or_none(country_result)
            country_name = country.name if country else "Unknown"
            
            # Create comprehensive business plan prompt
            business_plan_prompt = f"""
You are a professional business consultant creating a comprehensive business plan for an influencer. 

## Influencer Profile:
**Name:** {full_name}
**Email:** {email}
**Bio:** {bio}
**Website:** {website_url}
**Languages:** {languages}
**Base Country:** {country_name}
**Content Type:** {content_type}
**Base Rate:** ${base_rate}

## Task:
Create a detailed business plan that includes:

### 1. Executive Summary
- **Business Overview:** Influencer business model and value proposition
- **Mission Statement:** Clear mission and vision for the influencer brand
- **Key Objectives:** Primary business goals and success metrics
- **Unique Value Proposition:** What makes this influencer stand out

### 2. Market Analysis
- **Target Audience:** Detailed demographic and psychographic analysis
- **Market Size:** Addressable market for the influencer's niche
- **Competitive Landscape:** Analysis of similar influencers and competitors
- **Market Trends:** Current and emerging trends in the influencer space
- **Opportunity Assessment:** Market gaps and opportunities

### 3. Business Model
- **Revenue Streams:** Multiple income sources (sponsored content, affiliate marketing, etc.)
- **Pricing Strategy:** Rate structure and value-based pricing
- **Partnership Strategy:** Brand collaboration approach
- **Platform Strategy:** Multi-platform presence and optimization
- **Monetization Timeline:** Revenue growth projections

### 4. Marketing Strategy
- **Brand Positioning:** How to position the influencer in the market
- **Content Strategy:** Content themes, posting schedule, and engagement tactics
- **Growth Strategy:** Follower acquisition and retention strategies
- **Collaboration Strategy:** Brand partnership development
- **Crisis Management:** Reputation management and PR strategies

### 5. Financial Projections
- **Revenue Forecast:** 12-month revenue projections
- **Expense Structure:** Operating costs and investment requirements
- **Profitability Analysis:** Break-even analysis and profit margins
- **Cash Flow Management:** Financial planning and budgeting
- **Investment Requirements:** Funding needs and ROI projections

### 6. Operational Plan
- **Content Production:** Workflow and content creation processes
- **Technology Stack:** Tools and platforms for business operations
- **Team Structure:** Roles and responsibilities (if applicable)
- **Quality Control:** Standards and processes for content quality
- **Legal Compliance:** Contracts, disclosures, and regulatory requirements

### 7. Risk Analysis
- **Market Risks:** Platform changes, algorithm updates, market saturation
- **Operational Risks:** Content creation challenges, burnout, technical issues
- **Financial Risks:** Income volatility, payment delays, economic factors
- **Reputation Risks:** Controversy management and brand protection
- **Mitigation Strategies:** Risk management and contingency plans

### 8. Growth Strategy
- **Short-term Goals:** 3-6 month objectives and milestones
- **Medium-term Goals:** 6-12 month expansion plans
- **Long-term Vision:** 1-3 year strategic objectives
- **Scaling Strategy:** How to grow the business sustainably
- **Exit Strategy:** Future opportunities and potential exits

### 9. Implementation Timeline
- **Phase 1:** Foundation building (months 1-3)
- **Phase 2:** Growth and optimization (months 4-6)
- **Phase 3:** Expansion and diversification (months 7-12)
- **Key Milestones:** Critical success factors and checkpoints
- **Resource Allocation:** Time, money, and effort distribution

### 10. Success Metrics
- **KPIs:** Key performance indicators for business success
- **Measurement Tools:** Analytics and tracking systems
- **Reporting Schedule:** Regular review and assessment periods
- **Adjustment Process:** How to pivot based on performance data
- **Goal Achievement:** Success criteria and evaluation methods

Generate a professional, comprehensive business plan based on this detailed framework. Ensure each section contains specific, actionable insights and realistic strategies based on the provided influencer profile. Include practical examples, financial projections, and measurable goals. Make the plan highly personalized to the influencer's content type, rate, target audience, and market opportunities.
"""

            logger.info(f"Business plan prompt: {business_plan_prompt}")

            # Create template object
            template = SimpleNamespace(
                id='business_plan_template',
                prompt_text=business_plan_prompt,
                file_format=request.file_format,
                type='business_plan',
                subtype='influencer_plan'
            )
            
            # Parameters and related data
            parameters = {
                'influencer_name': full_name,
                'content_type': content_type,
                'base_rate': base_rate,
                'country': country_name,
                'file_format': request.file_format
            }
            
            related_data = {
                'user_id': 1 # Default user ID for public requests
            }
            
            # Generate document
            logger.info(f"Generating public business plan for influencer '{full_name}' (ID: {document_id})")
            file_path = generate_document(template, parameters, related_data)
            
            # Update with success
            doc.file_path = file_path
            doc.generation_status = 'completed'
            doc.generated_at = func.now()
            doc.updated_at = func.now()
            doc.parameters = parameters
            
            await db.commit()
            logger.info(f"Public business plan (ID: {document_id}) generated successfully: {file_path}")
            
        except Exception as e:
            logger.error(f"Public business plan generation failed for document ID {document_id}: {e}")
            
            try:
                doc.generation_status = 'failed'
                doc.error_message = str(e)
                doc.updated_at = func.now()
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update error status for document {document_id}: {db_error}")


@router.get("/{document_id}/status", response_model=Dict)
async def get_generation_status(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Check document generation status"""
    
    result = await db.execute(
        select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
    )
    doc = await safe_scalar_one_or_none(result)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    response_data = {
        "document_id": doc.id,
        "status": doc.generation_status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "user_id": doc.user_id,
        "type": doc.type,
        "subtype": doc.subtype
    }
    
    if doc.generation_status == 'completed':
        response_data.update({
            "file_path": doc.file_path,
            "generated_at": doc.generated_at.isoformat() if doc.generated_at else None,
            "download_url": f"/documents/{doc.id}/download",
            "parameters": doc.parameters
        })
    elif doc.generation_status == 'failed':
        response_data["error_message"] = doc.error_message
    elif doc.generation_status == 'processing':
        response_data["estimated_remaining"] = "15-45 seconds"
    elif doc.generation_status == 'pending':
        response_data["estimated_start"] = "5-10 seconds"
    
    return response_data


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download completed document"""
    
    result = await db.execute(
        select(GeneratedDocumentModel).where(
            GeneratedDocumentModel.id == document_id,
            GeneratedDocumentModel.generation_status == 'completed'
        )
    )
    doc = await safe_scalar_one_or_none(result)
    
    if not doc:
        raise HTTPException(
            status_code=404, 
            detail="Document not found or not ready. Check status first."
        )
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=404,
            detail="Document file not found on disk"
        )
    
    # Determine file extension and media type
    file_extension = doc.file_path.split('.')[-1].lower()
    media_types = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'html': 'text/html'
    }
    
    media_type = media_types.get(file_extension, 'application/octet-stream')
    
    return FileResponse(
        path=doc.file_path,
        filename=f"document_{document_id}.{file_extension}",
        media_type=media_type
    )


@router.get("/", response_model=List[Dict])
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    user_id: int = None,
    status_filter: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List documents with optional filtering"""
    
    query = select(GeneratedDocumentModel).order_by(GeneratedDocumentModel.created_at.desc())
    
    if user_id:
        query = query.where(GeneratedDocumentModel.user_id == user_id)
    
    if status_filter:
        query = query.where(GeneratedDocumentModel.generation_status == status_filter)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [
        {
            "document_id": doc.id,
            "status": doc.generation_status,
            "type": doc.type,
            "subtype": doc.subtype,
            "user_id": doc.user_id,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            "template_id": doc.template_id,
            "download_url": f"/documents/{doc.id}/download" if doc.generation_status == 'completed' else None,
            "status_url": f"/documents/{doc.id}/status"
        }
        for doc in documents
    ] 