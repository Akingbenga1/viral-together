from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
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
from typing import Dict, Annotated, List
from sqlalchemy import func
from types import SimpleNamespace
from datetime import datetime
from pydantic import BaseModel
import logging
import uuid
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

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
                    template = template_result.scalar_one_or_none()
                    
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
        influencer = influencer_result.scalar_one_or_none()
        
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
    business = business_result.scalar_one_or_none()
    
    influencer_result = await db.execute(
        select(Influencer).where(Influencer.id == request.influencer_id)
    )
    influencer = influencer_result.scalar_one_or_none()
    
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
    business = business_result.scalar_one_or_none()
    
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


@router.get("/{document_id}/status", response_model=Dict)
async def get_generation_status(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Check document generation status"""
    
    result = await db.execute(
        select(GeneratedDocumentModel).where(GeneratedDocumentModel.id == document_id)
    )
    doc = result.scalar_one_or_none()
    
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
    doc = result.scalar_one_or_none()
    
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