from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.services.document_generator import generate_document
from app.schemas.generated_documents import GeneratedDocument, GeneratedDocumentCreate
from app.db.models.generated_documents import GeneratedDocument as GeneratedDocumentModel
from app.db.models.document_templates import DocumentTemplate
from typing import Dict
from sqlalchemy import func

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/generate", response_model=GeneratedDocument)
async def generate_doc(request: GeneratedDocumentCreate, db: AsyncSession = Depends(get_db)):
    template_result = await db.execute(select(DocumentTemplate).where(DocumentTemplate.id == request.template_id))
    template = template_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    related_data: Dict = {}  # Fetch related data based on IDs (implement logic here)
    
    file_path = generate_document(template, request.parameters, related_data)
    
    new_doc = GeneratedDocumentModel(
        user_id=request.user_id,
        template_id=request.template_id,
        type=template.type,
        subtype=template.subtype,
        influencer_id=request.influencer_id,
        business_id=request.business_id,
        promotion_id=request.promotion_id,
        collaboration_id=request.collaboration_id,
        parameters=request.parameters,
        file_path=file_path,
        generation_status='generated',
        generated_at=func.now()
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    return new_doc 