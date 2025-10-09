"""
File downloads API endpoint for serving generated PDF files
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/downloads/files/{filename}")
async def download_file(filename: str):
    """
    Download a generated PDF file
    """
    try:
        # Security check - only allow PDF files
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Construct file path
        filepath = os.path.join("downloads", filename)
        
        # Check if file exists
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")