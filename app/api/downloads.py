"""
Downloads API endpoint for providing downloadable PDF guides
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging
import json
import os
from datetime import datetime

from app.db.session import get_db
from app.db.models.influencer_recommendation_summaries import InfluencerRecommendationSummaries

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/downloads")
async def get_download_files(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available download files for growth strategies
    """
    try:
        # Get the latest recommendation summary to generate download files
        from sqlalchemy import select, desc
        
        result = await db.execute(
            select(InfluencerRecommendationSummaries)
            .order_by(desc(InfluencerRecommendationSummaries.created_at))
        )
        latest_summary = result.scalar_one_or_none()
        
        if not latest_summary:
            return {
                "files": [],
                "message": "No growth strategies available. Generate strategies first to access download files."
            }
        
        # Use the actual download links from the database
        download_files = []
        
        if latest_summary.download_links:
            for i, link in enumerate(latest_summary.download_links, 1):
                download_files.append({
                    "id": i,
                    "title": link.get('title', 'Download File'),
                    "description": f"Download {link.get('title', 'file')}",
                    "category": link.get('category', 'General'),
                    "size": link.get('size', 'Unknown'),
                    "format": "PDF",
                    "downloadUrl": link.get('download_url', ''),
                    "available": True
                })
        
        return {
            "files": download_files,
            "total": len(download_files),
            "summary_id": latest_summary.id
        }
        
    except Exception as e:
        logger.error(f"Error fetching download files: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch download files: {str(e)}")

@router.get("/downloads/pdf/{category}/{summary_id}")
async def download_pdf(
    category: str,
    summary_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Download PDF for a specific category and summary ID
    """
    try:
        # Get the specific summary
        from sqlalchemy import select
        
        result = await db.execute(
            select(InfluencerRecommendationSummaries)
            .where(InfluencerRecommendationSummaries.id == summary_id)
        )
        summary = result.scalar_one_or_none()
        
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        
        # Generate PDF content based on category
        pdf_content = generate_pdf_content(category, summary)
        
        # Create PDF file
        filename = f"{category}_{summary_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = f"downloads/{filename}"
        
        # Ensure downloads directory exists
        os.makedirs("downloads", exist_ok=True)
        
        # Write content to file (for now as text, in production would be actual PDF)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(pdf_content)
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF for {category}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

def generate_pdf_content(category: str, summary: InfluencerRecommendationSummaries) -> str:
    """
    Generate PDF content based on category and summary data using templates
    """
    content = f"# {category.replace('_', ' ').title()} Implementation Guide\n\n"
    content += f"Generated on: {summary.created_at}\n\n"
    
    # Get the actual data from the database column
    data = None
    if category == "more_followers":
        data = summary.more_followers
    elif category == "content_ideas":
        data = summary.content_ideas
    elif category == "social_profiles":
        data = summary.social_profiles
    elif category == "influencer_collab":
        data = summary.influencer_collab
    elif category == "business_collab":
        data = summary.business_collab
    elif category == "content_scripts":
        data = summary.content_scripts
    
    if not data:
        content += f"No {category} data available.\n"
        return content
    
    # Parse the JSON data and format it using templates
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        content += f"## Implementation Steps\n\n"
        
        # Use template to format the data
        if isinstance(data, list):
            for i, item in enumerate(data, 1):
                content += f"### Step {i}\n\n"
                if isinstance(item, dict):
                    for key, value in item.items():
                        content += f"**{key.replace('_', ' ').title()}:** {value}\n\n"
                else:
                    content += f"{item}\n\n"
        elif isinstance(data, dict):
            for key, value in data.items():
                content += f"### {key.replace('_', ' ').title()}\n\n"
                if isinstance(value, list):
                    for i, item in enumerate(value, 1):
                        content += f"{i}. {item}\n"
                    content += "\n"
                else:
                    content += f"{value}\n\n"
        else:
            content += f"{data}\n\n"
            
    except json.JSONDecodeError:
        # If not JSON, treat as plain text
        content += f"{data}\n\n"
    except Exception as e:
        content += f"Error processing data: {str(e)}\n\n"
    
    return content
