from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.schemas.document_templates import DocumentTemplateCreate, DocumentTemplate
from app.db.models.document_templates import DocumentTemplate as DocumentTemplateModel
from app.core.dependencies import require_role
from app.schemas.user import UserRead
from typing import List, Dict, Optional
from pydantic import BaseModel
import json
import asyncio
import aiohttp
import aiofiles
import os
from pathlib import Path
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AutoSourceRequest(BaseModel):
    template_types: Optional[List[str]] = None

router = APIRouter(prefix="/document-templates", tags=["document-templates"])

# Admin-only template upload endpoint
@router.post("/upload", response_model=DocumentTemplate, status_code=status.HTTP_201_CREATED)
async def upload_document_template(
    name: str,
    type: str,
    subtype: Optional[str] = None,
    file_format: str = "pdf",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_role("admin"))
):
    """Admin-only endpoint to upload document templates from files"""
    
    # Validate file type
    allowed_extensions = {".txt", ".docx", ".pdf", ".html", ".json"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Check for duplicate template name
    existing_template = await db.execute(
        select(DocumentTemplateModel).where(
            DocumentTemplateModel.name == name,
            DocumentTemplateModel.is_active == True
        )
    )
    if existing_template.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A document template with this name already exists"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process content based on file type
        if file_extension == ".json":
            # JSON template format
            template_data = json.loads(content.decode('utf-8'))
            prompt_text = template_data.get('prompt_text', '')
            default_parameters = template_data.get('default_parameters', {})
        else:
            # Plain text/document content
            prompt_text = content.decode('utf-8')
            default_parameters = {}
        
        # Save uploaded file to storage
        upload_dir = Path("app/static/templates/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = upload_dir / unique_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Create document template
        db_template = DocumentTemplateModel(
            name=name,
            type=type,
            subtype=subtype,
            prompt_text=prompt_text,
            default_parameters=default_parameters,
            file_format=file_format,
            created_by=current_user.id,
            is_active=True
        )
        
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        
        logger.info(f"Template '{name}' uploaded successfully by admin user {current_user.id}")
        return db_template
        
    except Exception as e:
        logger.error(f"Error uploading template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded template"
        )

# Automatic online template sourcing
@router.post("/auto-source", response_model=Dict)
async def auto_source_templates(
    request: AutoSourceRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_role("admin"))
):
    """Admin endpoint to automatically source templates from online repositories"""
    
    template_types = request.template_types
    if not template_types:
        template_types = ["contract", "agreement", "invoice", "proposal", "nda"]
    
    # Add background task for sourcing
    background_tasks.add_task(
        source_templates_from_online,
        db,
        current_user.id,
        template_types
    )
    
    return {"message": "Template sourcing started in background", "types": template_types}

async def source_templates_from_online(
    db: AsyncSession,
    admin_user_id: int,
    template_types: List[str]
):
    """Background task to source templates from various online sources"""
    
    # Template sources configuration
    TEMPLATE_SOURCES = {
        "github_legal_templates": {
            "base_url": "https://raw.githubusercontent.com/seriohub/legal-docs/main/templates",
            "templates": {
                "contract": "influencer_contract_template.txt",
                "nda": "nda_template.txt",
                "agreement": "collaboration_agreement.txt"
            }
        },
        "template_api": {
            "base_url": "https://api.legal-templates.com/v1",
            "endpoint": "/templates",
            "api_key": os.getenv("LEGAL_TEMPLATES_API_KEY")  # Optional API
        }
    }
    
    sourced_templates = []
    
    try:
        async with aiohttp.ClientSession() as session:
            for template_type in template_types:
                # Try GitHub source first
                await _source_from_github(
                    session, db, admin_user_id, template_type, 
                    TEMPLATE_SOURCES["github_legal_templates"], sourced_templates
                )
                
                # Try template API if available
                if TEMPLATE_SOURCES["template_api"]["api_key"]:
                    await _source_from_api(
                        session, db, admin_user_id, template_type,
                        TEMPLATE_SOURCES["template_api"], sourced_templates
                    )
        
        logger.info(f"Successfully sourced {len(sourced_templates)} templates")
        
    except Exception as e:
        logger.error(f"Error in auto-sourcing templates: {str(e)}")

async def _source_from_github(
    session: aiohttp.ClientSession,
    db: AsyncSession,
    admin_user_id: int,
    template_type: str,
    source_config: Dict,
    sourced_templates: List
):
    """Source templates from GitHub repositories"""
    
    if template_type not in source_config["templates"]:
        return
    
    template_file = source_config["templates"][template_type]
    url = f"{source_config['base_url']}/{template_file}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                
                # Check if template already exists
                template_name = f"Auto_{template_type.title()}_Template_{datetime.now().strftime('%Y%m%d')}"
                
                existing = await db.execute(
                    select(DocumentTemplateModel).where(
                        DocumentTemplateModel.name == template_name
                    )
                )
                
                if not existing.scalar_one_or_none():
                    # Create new template
                    db_template = DocumentTemplateModel(
                        name=template_name,
                        type=template_type,
                        subtype="auto_sourced",
                        prompt_text=content,
                        default_parameters={
                            "source": "github",
                            "source_url": url,
                            "auto_generated": True
                        },
                        file_format="pdf",
                        created_by=admin_user_id,
                        is_active=True
                    )
                    
                    db.add(db_template)
                    await db.commit()
                    sourced_templates.append(db_template)
                    
                    logger.info(f"Sourced template from GitHub: {template_name}")
    
    except Exception as e:
        logger.error(f"Error sourcing from GitHub: {str(e)}")

async def _source_from_api(
    session: aiohttp.ClientSession,
    db: AsyncSession,
    admin_user_id: int,
    template_type: str,
    api_config: Dict,
    sourced_templates: List
):
    """Source templates from template APIs"""
    
    headers = {"Authorization": f"Bearer {api_config['api_key']}"}
    params = {"type": template_type, "format": "text"}
    url = f"{api_config['base_url']}{api_config['endpoint']}"
    
    try:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                for template_data in data.get("templates", []):
                    template_name = f"API_{template_data.get('name', template_type).title()}_{datetime.now().strftime('%Y%m%d')}"
                    
                    # Check if template already exists
                    existing = await db.execute(
                        select(DocumentTemplateModel).where(
                            DocumentTemplateModel.name == template_name
                        )
                    )
                    
                    if not existing.scalar_one_or_none():
                        db_template = DocumentTemplateModel(
                            name=template_name,
                            type=template_type,
                            subtype="api_sourced",
                            prompt_text=template_data.get('content', ''),
                            default_parameters={
                                "source": "api",
                                "api_source": api_config['base_url'],
                                "auto_generated": True,
                                **template_data.get('parameters', {})
                            },
                            file_format="pdf",
                            created_by=admin_user_id,
                            is_active=True
                        )
                        
                        db.add(db_template)
                        await db.commit()
                        sourced_templates.append(db_template)
                        
                        logger.info(f"Sourced template from API: {template_name}")
    
    except Exception as e:
        logger.error(f"Error sourcing from API: {str(e)}")

# Get templates with source information
@router.get("/", response_model=List[DocumentTemplate])
async def get_document_templates(
    skip: int = 0,
    limit: int = 100,
    template_type: str = None,
    source_type: str = None,  # filter by source (uploaded, auto_sourced, api_sourced)
    db: AsyncSession = Depends(get_db)
):
    """Get document templates with optional filtering by source type"""
    
    query = select(DocumentTemplateModel).where(DocumentTemplateModel.is_active == True)
    
    if template_type:
        query = query.where(DocumentTemplateModel.type == template_type)
    
    if source_type:
        query = query.where(DocumentTemplateModel.subtype == source_type)
    
    query = query.offset(skip).limit(limit).order_by(DocumentTemplateModel.created_at.desc())
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return templates

@router.get("/{template_id}", response_model=DocumentTemplate)
async def get_document_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document template by ID"""
    
    result = await db.execute(
        select(DocumentTemplateModel).where(
            DocumentTemplateModel.id == template_id,
            DocumentTemplateModel.is_active == True
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document template not found"
        )
    
    return template

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(require_role("admin"))
):
    """Admin-only endpoint to soft delete a document template"""
    
    result = await db.execute(
        select(DocumentTemplateModel).where(DocumentTemplateModel.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document template not found"
        )
    
    template.is_active = False
    await db.commit()
    
    logger.info(f"Template {template_id} soft deleted by admin user {current_user.id}") 