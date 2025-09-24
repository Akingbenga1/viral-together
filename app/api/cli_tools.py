"""
CLI Tools API Endpoints
FastAPI endpoints for testing CLI tool functionality
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
import logging
import asyncio
import os
from pathlib import Path

from ..core.dependencies import get_current_user
from ..services.cli_tools import CLIToolAgentService, GenerationResult
from ..schemas.user import User

logger = logging.getLogger(__name__)

# Initialize CLI Tool Agent Service
cli_agent_service = CLIToolAgentService()

router = APIRouter(prefix="/cli-tools", tags=["CLI Tools"])

# Request Models
class DocumentRequest(BaseModel):
    type: str = Field(..., description="Document type: markdown, pdf_from_markdown, latex, pdf_from_latex, word, powerpoint, excel")
    content: str = Field(..., description="Document content")
    filename: Optional[str] = Field(None, description="Output filename")
    slides: Optional[List[Dict[str, Any]]] = Field(None, description="Slides data for PowerPoint")
    data: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="Data for Excel")

class ImageRequest(BaseModel):
    type: str = Field(default="from_prompt", description="Image type: from_prompt, batch")
    prompt: str = Field(..., description="Text prompt for image generation")
    width: int = Field(default=512, ge=64, le=2048)
    height: int = Field(default=512, ge=64, le=2048)
    filename: Optional[str] = Field(None, description="Output filename")
    prompts: Optional[List[str]] = Field(None, description="Multiple prompts for batch generation")
    output_dir: Optional[str] = Field(None, description="Output directory for batch")

class VideoRequest(BaseModel):
    type: str = Field(..., description="Video type: text_video, images_to_video, add_audio, concatenate, resize")
    filename: Optional[str] = Field(None, description="Output filename")
    text: Optional[str] = Field(None, description="Text for text video")
    duration: Optional[float] = Field(5.0, description="Duration in seconds")
    font_size: Optional[int] = Field(48, description="Font size for text video")
    image_paths: Optional[List[str]] = Field(None, description="Image paths for slideshow")
    duration_per_image: Optional[float] = Field(2.0, description="Duration per image")
    video_path: Optional[str] = Field(None, description="Input video path")
    audio_path: Optional[str] = Field(None, description="Audio path")
    video_paths: Optional[List[str]] = Field(None, description="Video paths for concatenation")
    input_path: Optional[str] = Field(None, description="Input path for resize")
    width: Optional[int] = Field(1280, description="Width for resize")
    height: Optional[int] = Field(720, description="Height for resize")

class AudioRequest(BaseModel):
    type: str = Field(..., description="Audio type: text_to_speech, silence, concatenate")
    filename: Optional[str] = Field(None, description="Output filename")
    text: Optional[str] = Field(None, description="Text for TTS")
    voice: str = Field(default="default", description="Voice for TTS")
    speed: float = Field(default=1.0, description="Speech speed")
    duration: Optional[float] = Field(None, description="Duration for silence")
    audio_paths: Optional[List[str]] = Field(None, description="Audio paths for concatenation")

class MultimediaRequest(BaseModel):
    user_prompt: str = Field(..., description="User request prompt")
    content_types: Optional[List[str]] = Field(None, description="Content types to generate")
    documents: Optional[List[DocumentRequest]] = None
    images: Optional[List[ImageRequest]] = None
    videos: Optional[List[VideoRequest]] = None
    audio: Optional[List[AudioRequest]] = None

# System Status Endpoints
@router.get("/system/status")
async def get_system_status(current_user: User = Depends(get_current_user)):
    """Get comprehensive system status for CLI tools"""
    try:
        status = await cli_agent_service.get_system_status()
        return {
            "success": True,
            "system_status": status
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/readiness")
async def check_system_readiness(current_user: User = Depends(get_current_user)):
    """Check system readiness for different types of generation"""
    try:
        readiness = await cli_agent_service.check_readiness()
        return {
            "success": True,
            "readiness": readiness
        }
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/installation-guide")
async def get_installation_guide(current_user: User = Depends(get_current_user)):
    """Get installation suggestions for missing tools"""
    try:
        guide = await cli_agent_service.get_installation_guide()
        return {
            "success": True,
            "installation_guide": guide
        }
    except Exception as e:
        logger.error(f"Installation guide error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document Generation Endpoints
@router.post("/generate/document")
async def generate_document(
    request: DocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate document using CLI tools"""
    try:
        result = await cli_agent_service.generate_document(request.dict())
        
        if result.success:
            return {
                "success": True,
                "file_path": result.file_path,
                "metadata": result.metadata
            }
        else:
            return {
                "success": False,
                "error": result.error_message
            }
            
    except Exception as e:
        logger.error(f"Document generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/document/{filename}")
async def download_document(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download generated document"""
    try:
        file_path = cli_agent_service.output_base_dir / "documents" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Document download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Image Generation Endpoints
@router.post("/generate/image")
async def generate_image(
    request: ImageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate image using Stable Diffusion"""
    try:
        result = await cli_agent_service.generate_image(request.dict())
        
        if result.success:
            return {
                "success": True,
                "file_path": result.file_path,
                "metadata": result.metadata
            }
        else:
            return {
                "success": False,
                "error": result.error_message
            }
            
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/image/{filename}")
async def download_image(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download generated image"""
    try:
        file_path = cli_agent_service.output_base_dir / "images" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='image/png'
        )
        
    except Exception as e:
        logger.error(f"Image download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Video Generation Endpoints
@router.post("/generate/video")
async def generate_video(
    request: VideoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate video using FFMPEG"""
    try:
        result = await cli_agent_service.generate_video(request.dict())
        
        if result.success:
            return {
                "success": True,
                "file_path": result.file_path,
                "metadata": result.metadata
            }
        else:
            return {
                "success": False,
                "error": result.error_message
            }
            
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/video/{filename}")
async def download_video(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download generated video"""
    try:
        file_path = cli_agent_service.output_base_dir / "videos" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"Video download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Audio Generation Endpoints
@router.post("/generate/audio")
async def generate_audio(
    request: AudioRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate audio using TTS"""
    try:
        result = await cli_agent_service.generate_audio(request.dict())
        
        if result.success:
            return {
                "success": True,
                "file_path": result.file_path,
                "metadata": result.metadata
            }
        else:
            return {
                "success": False,
                "error": result.error_message
            }
            
    except Exception as e:
        logger.error(f"Audio generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/audio/{filename}")
async def download_audio(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download generated audio"""
    try:
        file_path = cli_agent_service.output_base_dir / "audio" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='audio/wav'
        )
        
    except Exception as e:
        logger.error(f"Audio download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Multimedia Generation Endpoints
@router.post("/generate/multimedia")
async def generate_multimedia_content(
    request: MultimediaRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate multiple types of content in one operation"""
    try:
        results = await cli_agent_service.generate_multimedia_content(request.dict())
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Multimedia generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Agent Integration Endpoints
@router.post("/ai-agent/process")
async def process_ai_agent_request(
    user_prompt: str,
    content_types: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """Process AI agent request and generate content"""
    try:
        result = await cli_agent_service.process_ai_request(user_prompt, content_types)
        
        return {
            "success": True,
            "ai_response": result
        }
        
    except Exception as e:
        logger.error(f"AI agent processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@router.post("/session/start")
async def start_generation_session(current_user: User = Depends(get_current_user)):
    """Start a new generation session"""
    try:
        session_id = await cli_agent_service.start_generation_session()
        return {
            "success": True,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Session start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/end")
async def end_generation_session(current_user: User = Depends(get_current_user)):
    """End current generation session"""
    try:
        summary = await cli_agent_service.end_generation_session()
        return {
            "success": True,
            "session_summary": summary
        }
    except Exception as e:
        logger.error(f"Session end error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File Management Endpoints
@router.get("/files/list")
async def list_generated_files(current_user: User = Depends(get_current_user)):
    """List all generated files"""
    try:
        files = {}
        base_dir = cli_agent_service.output_base_dir
        
        for content_type in ["documents", "images", "videos", "audio"]:
            type_dir = base_dir / content_type
            if type_dir.exists():
                files[content_type] = [
                    {
                        "filename": f.name,
                        "size": f.stat().st_size,
                        "created": f.stat().st_ctime,
                        "path": str(f.relative_to(base_dir))
                    }
                    for f in type_dir.glob("*")
                    if f.is_file()
                ]
            else:
                files[content_type] = []
        
        return {
            "success": True,
            "files": files
        }
        
    except Exception as e:
        logger.error(f"File listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{content_type}/{filename}")
async def delete_generated_file(
    content_type: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a generated file"""
    try:
        if content_type not in ["documents", "images", "videos", "audio"]:
            raise HTTPException(status_code=400, detail="Invalid content type")
        
        file_path = cli_agent_service.output_base_dir / content_type / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path.unlink()
        
        return {
            "success": True,
            "message": f"File {filename} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"File deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup endpoint
@router.post("/cleanup")
async def cleanup_resources(current_user: User = Depends(get_current_user)):
    """Cleanup CLI tool resources"""
    try:
        cli_agent_service.cleanup()
        return {
            "success": True,
            "message": "Resources cleaned up successfully"
        }
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))