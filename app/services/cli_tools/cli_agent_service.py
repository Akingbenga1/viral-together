"""
CLI Tool AI Agent Service
Main orchestration service for CLI-based content generation
Following SOLID principles - Single Responsibility, Dependency Inversion
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import uuid

from .interfaces import (
    IDocumentGenerator, IVideoGenerator, IImageGenerator, IAudioGenerator, 
    ICLIToolChecker, GenerationResult
)
from .document_generator import DocumentGenerationService
from .video_generator import VideoGenerationService
from .image_generator import ImageGenerationService
from .audio_generator import AudioGenerationService
from .tool_checker import CLIToolChecker

logger = logging.getLogger(__name__)

class CLIToolAgentService:
    """
    Main CLI Tool Agent Service for content generation
    Follows SOLID principles:
    - Single Responsibility: Orchestrates different content generation services
    - Open/Closed: Can be extended with new generators via interfaces
    - Liskov Substitution: All generators implement their respective interfaces
    - Interface Segregation: Separate interfaces for each type of generation
    - Dependency Inversion: Depends on abstractions (interfaces) not concretions
    """
    
    def __init__(self, 
                 output_base_dir: str = "/tmp/cli_generations",
                 document_generator: Optional[IDocumentGenerator] = None,
                 video_generator: Optional[IVideoGenerator] = None,
                 image_generator: Optional[IImageGenerator] = None,
                 audio_generator: Optional[IAudioGenerator] = None,
                 tool_checker: Optional[ICLIToolChecker] = None):
        
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Dependency Injection - using interfaces
        self.document_generator = document_generator or DocumentGenerationService(
            output_dir=str(self.output_base_dir / "documents")
        )
        self.video_generator = video_generator or VideoGenerationService(
            output_dir=str(self.output_base_dir / "videos")
        )
        self.image_generator = image_generator or ImageGenerationService(
            output_dir=str(self.output_base_dir / "images")
        )
        self.audio_generator = audio_generator or AudioGenerationService(
            output_dir=str(self.output_base_dir / "audio")
        )
        self.tool_checker = tool_checker or CLIToolChecker()
        
        # Session management
        self.current_session_id = None
        self.session_history: List[Dict[str, Any]] = []
    
    async def start_generation_session(self) -> str:
        """Start a new generation session"""
        self.current_session_id = f"cli_session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        session_dir = self.output_base_dir / self.current_session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Started CLI generation session: {self.current_session_id}")
        return self.current_session_id
    
    async def end_generation_session(self) -> Dict[str, Any]:
        """End current generation session and return summary"""
        if not self.current_session_id:
            return {"error": "No active session"}
        
        summary = {
            "session_id": self.current_session_id,
            "ended_at": datetime.now().isoformat(),
            "total_operations": len(self.session_history),
            "operations": self.session_history,
            "output_directory": str(self.output_base_dir / self.current_session_id)
        }
        
        # Reset session
        self.current_session_id = None
        self.session_history = []
        
        return summary
    
    def _log_operation(self, operation_type: str, operation_name: str, 
                      result: GenerationResult, **metadata):
        """Log operation to session history"""
        if self.current_session_id:
            self.session_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": operation_type,
                "operation": operation_name,
                "success": result.success,
                "output_file": result.file_path if result.success else None,
                "error": result.error_message if not result.success else None,
                "metadata": {**result.metadata, **metadata}
            })
    
    # Document Generation Methods
    async def generate_document(self, request: Dict[str, Any]) -> GenerationResult:
        """Generate document based on request parameters"""
        doc_type = request.get("type", "markdown")
        content = request.get("content", "")
        filename = request.get("filename", f"document_{uuid.uuid4().hex[:8]}")
        
        if self.current_session_id:
            filename = f"{self.current_session_id}_{filename}"
        
        result = None
        
        if doc_type == "markdown":
            result = await self.document_generator.generate_markdown(content, filename)
        elif doc_type == "pdf_from_markdown":
            result = await self.document_generator.generate_pdf_from_markdown(content, filename)
        elif doc_type == "latex":
            result = await self.document_generator.generate_latex(content, filename)
        elif doc_type == "pdf_from_latex":
            result = await self.document_generator.generate_pdf_from_latex(content, filename)
        elif doc_type == "word":
            result = await self.document_generator.generate_word_document(content, filename)
        elif doc_type == "powerpoint":
            slides = request.get("slides", [{"title": "Generated Slide", "content": content}])
            result = await self.document_generator.generate_powerpoint(slides, filename)
        elif doc_type == "excel":
            data = request.get("data", {"Sheet1": [{"Column1": content}]})
            result = await self.document_generator.generate_excel(data, filename)
        else:
            result = GenerationResult(success=False, error_message=f"Unsupported document type: {doc_type}")
        
        self._log_operation("document", doc_type, result, request=request)
        return result
    
    # Video Generation Methods
    async def generate_video(self, request: Dict[str, Any]) -> GenerationResult:
        """Generate video based on request parameters"""
        video_type = request.get("type", "text_video")
        filename = request.get("filename", f"video_{uuid.uuid4().hex[:8]}")
        
        if self.current_session_id:
            filename = f"{self.current_session_id}_{filename}"
        
        result = None
        
        if video_type == "text_video":
            text = request.get("text", "Generated Video")
            duration = request.get("duration", 5.0)
            font_size = request.get("font_size", 48)
            result = await self.video_generator.create_text_video(text, filename, duration, font_size)
            
        elif video_type == "images_to_video":
            image_paths = request.get("image_paths", [])
            duration_per_image = request.get("duration_per_image", 2.0)
            result = await self.video_generator.create_video_from_images(image_paths, filename, duration_per_image)
            
        elif video_type == "add_audio":
            video_path = request.get("video_path", "")
            audio_path = request.get("audio_path", "")
            result = await self.video_generator.add_audio_to_video(video_path, audio_path, filename)
            
        elif video_type == "concatenate":
            video_paths = request.get("video_paths", [])
            result = await self.video_generator.concatenate_videos(video_paths, filename)
            
        elif video_type == "resize":
            input_path = request.get("input_path", "")
            width = request.get("width", 1280)
            height = request.get("height", 720)
            result = await self.video_generator.resize_video(input_path, filename, width, height)
            
        else:
            result = GenerationResult(success=False, error_message=f"Unsupported video type: {video_type}")
        
        self._log_operation("video", video_type, result, request=request)
        return result
    
    # Image Generation Methods
    async def generate_image(self, request: Dict[str, Any]) -> GenerationResult:
        """Generate image based on request parameters"""
        image_type = request.get("type", "from_prompt")
        filename = request.get("filename", f"image_{uuid.uuid4().hex[:8]}")
        
        if self.current_session_id:
            filename = f"{self.current_session_id}_{filename}"
        
        result = None
        
        if image_type == "from_prompt":
            prompt = request.get("prompt", "A beautiful landscape")
            width = request.get("width", 512)
            height = request.get("height", 512)
            result = await self.image_generator.generate_from_prompt(prompt, filename, width, height)
            
        elif image_type == "batch":
            prompts = request.get("prompts", ["A beautiful landscape"])
            output_dir = request.get("output_dir", str(self.output_base_dir / "images" / "batch"))
            width = request.get("width", 512)
            height = request.get("height", 512)
            results = await self.image_generator.generate_batch(prompts, output_dir, width, height)
            # Return first result for consistency, but log all
            result = results[0] if results else GenerationResult(success=False, error_message="No results")
        
        elif image_type == "chart":
            chart_type = request.get("chart_type", "bar")
            data = request.get("data", {"labels": ["A", "B", "C"], "values": [1, 2, 3]})
            width = request.get("width", 800)
            height = request.get("height", 600)
            result = await self.image_generator.generate_chart_image(data, chart_type, filename, width, height)
        
        elif image_type == "logo":
            text = request.get("text", "Logo Text")
            width = request.get("width", 400)
            height = request.get("height", 200)
            result = await self.image_generator.generate_logo_style_image(text, filename, width, height)
            
        else:
            result = GenerationResult(success=False, error_message=f"Unsupported image type: {image_type}")
        
        self._log_operation("image", image_type, result, request=request)
        return result
    
    # Audio Generation Methods
    async def generate_audio(self, request: Dict[str, Any]) -> GenerationResult:
        """Generate audio based on request parameters"""
        audio_type = request.get("type", "text_to_speech")
        filename = request.get("filename", f"audio_{uuid.uuid4().hex[:8]}")
        
        if self.current_session_id:
            filename = f"{self.current_session_id}_{filename}"
        
        result = None
        
        if audio_type == "text_to_speech":
            text = request.get("text", "Hello, this is generated speech")
            voice = request.get("voice", "default")
            speed = request.get("speed", 1.0)
            result = await self.audio_generator.text_to_speech(text, filename, voice, speed)
            
        elif audio_type == "silence":
            duration = request.get("duration", 5.0)
            result = await self.audio_generator.generate_silence(duration, filename)
            
        elif audio_type == "concatenate":
            audio_paths = request.get("audio_paths", [])
            result = await self.audio_generator.concatenate_audio(audio_paths, filename)
            
        else:
            result = GenerationResult(success=False, error_message=f"Unsupported audio type: {audio_type}")
        
        self._log_operation("audio", audio_type, result, request=request)
        return result
    
    # Multi-modal Generation Methods
    async def generate_multimedia_content(self, request: Dict[str, Any]) -> Dict[str, GenerationResult]:
        """Generate multiple types of content in one operation"""
        results = {}
        
        # Start session if not already active
        if not self.current_session_id:
            await self.start_generation_session()
        
        # Generate documents
        if "documents" in request:
            results["documents"] = []
            for doc_request in request["documents"]:
                result = await self.generate_document(doc_request)
                results["documents"].append(result)
        
        # Generate images
        if "images" in request:
            results["images"] = []
            for img_request in request["images"]:
                result = await self.generate_image(img_request)
                results["images"].append(result)
        
        # Generate audio
        if "audio" in request:
            results["audio"] = []
            for audio_request in request["audio"]:
                result = await self.generate_audio(audio_request)
                results["audio"].append(result)
        
        # Generate videos
        if "videos" in request:
            results["videos"] = []
            for video_request in request["videos"]:
                result = await self.generate_video(video_request)
                results["videos"].append(result)
        
        return results
    
    # AI Agent Integration Methods
    async def process_ai_request(self, user_prompt: str, content_types: List[str] = None) -> Dict[str, Any]:
        """Process AI agent request and determine what to generate"""
        # This would integrate with the AI agent to understand the request
        # For now, we'll create a simple parser
        
        if content_types is None:
            content_types = self._analyze_request_for_content_types(user_prompt)
        
        generation_requests = self._create_generation_requests(user_prompt, content_types)
        
        # Start session
        session_id = await self.start_generation_session()
        
        # Generate content
        results = await self.generate_multimedia_content(generation_requests)
        
        # End session and get summary
        session_summary = await self.end_generation_session()
        
        return {
            "session_id": session_id,
            "user_prompt": user_prompt,
            "content_types": content_types,
            "results": results,
            "session_summary": session_summary
        }
    
    def _analyze_request_for_content_types(self, user_prompt: str) -> List[str]:
        """Analyze user prompt to determine what content types to generate"""
        content_types = []
        prompt_lower = user_prompt.lower()
        
        # Document generation keywords
        if any(word in prompt_lower for word in ["document", "pdf", "report", "markdown", "word", "powerpoint", "excel", "presentation"]):
            content_types.append("document")
        
        # Image generation keywords
        if any(word in prompt_lower for word in ["image", "picture", "photo", "visual", "illustration", "graphic"]):
            content_types.append("image")
        
        # Video generation keywords
        if any(word in prompt_lower for word in ["video", "movie", "clip", "animation", "slideshow"]):
            content_types.append("video")
        
        # Audio generation keywords
        if any(word in prompt_lower for word in ["audio", "speech", "voice", "sound", "narration", "tts"]):
            content_types.append("audio")
        
        # Default to document if no specific type detected
        if not content_types:
            content_types.append("document")
        
        return content_types
    
    def _create_generation_requests(self, user_prompt: str, content_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Create generation requests based on user prompt and content types"""
        requests = {}
        
        if "document" in content_types:
            requests["documents"] = [{
                "type": "markdown",
                "content": f"# Generated Content\n\n{user_prompt}\n\nThis document was generated based on the user request.",
                "filename": "ai_generated_document"
            }]
        
        if "image" in content_types:
            requests["images"] = [{
                "type": "from_prompt",
                "prompt": f"Professional illustration representing: {user_prompt}",
                "width": 1024,
                "height": 768,
                "filename": "ai_generated_image"
            }]
        
        if "audio" in content_types:
            requests["audio"] = [{
                "type": "text_to_speech",
                "text": user_prompt,
                "voice": "default",
                "speed": 1.0,
                "filename": "ai_generated_audio"
            }]
        
        if "video" in content_types:
            requests["videos"] = [{
                "type": "text_video",
                "text": user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt,
                "duration": 10.0,
                "font_size": 36,
                "filename": "ai_generated_video"
            }]
        
        return requests
    
    # System Status Methods
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return await self.tool_checker.get_comprehensive_status()
    
    async def get_installation_guide(self) -> Dict[str, List[str]]:
        """Get installation suggestions for missing tools"""
        return await self.tool_checker.get_installation_suggestions()
    
    async def check_readiness(self) -> Dict[str, bool]:
        """Check if system is ready for different types of generation"""
        readiness = {
            "document_generation": True,  # Always available (basic text files)
            "pdf_generation": await self.tool_checker.check_tool_availability("pandoc"),
            "latex_generation": await self.tool_checker.check_tool_availability("pdflatex"),
            "office_documents": await self.tool_checker.check_tool_availability("python-docx"),
            "image_generation": await self.tool_checker.check_tool_availability("diffusers"),
            "video_generation": await self.tool_checker.check_tool_availability("ffmpeg"),
            "audio_generation": (
                await self.tool_checker.check_tool_availability("pyttsx3") or
                await self.tool_checker.check_tool_availability("espeak") or
                await self.tool_checker.check_tool_availability("festival")
            )
        }
        
        return readiness
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self.image_generator, 'cleanup'):
            self.image_generator.cleanup()