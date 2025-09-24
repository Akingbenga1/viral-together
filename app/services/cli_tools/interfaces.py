"""
CLI Tool Service Interfaces
Following SOLID principles - Interface Segregation Principle
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import asyncio
from enum import Enum

class OutputFormat(Enum):
    PDF = "pdf"
    DOCX = "docx" 
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    MARKDOWN = "md"
    LATEX = "tex"
    TXT = "txt"
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"

class GenerationResult:
    """Result container for generation operations"""
    def __init__(self, 
                 success: bool, 
                 file_path: Optional[str] = None, 
                 error_message: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.file_path = file_path
        self.error_message = error_message
        self.metadata = metadata or {}

class IDocumentGenerator(ABC):
    """Interface for document generation services"""
    
    @abstractmethod
    async def generate_markdown(self, content: str, output_path: str) -> GenerationResult:
        """Generate markdown document"""
        pass
    
    @abstractmethod
    async def generate_pdf_from_markdown(self, markdown_content: str, output_path: str) -> GenerationResult:
        """Generate PDF from markdown using Pandoc"""
        pass
    
    @abstractmethod
    async def generate_latex(self, content: str, output_path: str) -> GenerationResult:
        """Generate LaTeX document"""
        pass
    
    @abstractmethod
    async def generate_pdf_from_latex(self, latex_content: str, output_path: str) -> GenerationResult:
        """Generate PDF from LaTeX"""
        pass
    
    @abstractmethod
    async def generate_word_document(self, content: str, output_path: str) -> GenerationResult:
        """Generate Word document"""
        pass
    
    @abstractmethod
    async def generate_powerpoint(self, slides_data: List[Dict[str, Any]], output_path: str) -> GenerationResult:
        """Generate PowerPoint presentation"""
        pass
    
    @abstractmethod
    async def generate_excel(self, data: Dict[str, List[Dict[str, Any]]], output_path: str) -> GenerationResult:
        """Generate Excel spreadsheet"""
        pass

class IVideoGenerator(ABC):
    """Interface for video generation services"""
    
    @abstractmethod
    async def create_video_from_images(self, image_paths: List[str], output_path: str, 
                                     duration_per_image: float = 2.0) -> GenerationResult:
        """Create video from sequence of images"""
        pass
    
    @abstractmethod
    async def add_audio_to_video(self, video_path: str, audio_path: str, output_path: str) -> GenerationResult:
        """Add audio track to video"""
        pass
    
    @abstractmethod
    async def create_text_video(self, text: str, output_path: str, 
                              duration: float = 5.0, font_size: int = 48) -> GenerationResult:
        """Create video with text overlay"""
        pass
    
    @abstractmethod
    async def concatenate_videos(self, video_paths: List[str], output_path: str) -> GenerationResult:
        """Concatenate multiple videos"""
        pass
    
    @abstractmethod
    async def resize_video(self, input_path: str, output_path: str, width: int, height: int) -> GenerationResult:
        """Resize video to specified dimensions"""
        pass

class IImageGenerator(ABC):
    """Interface for image generation services"""
    
    @abstractmethod
    async def generate_from_prompt(self, prompt: str, output_path: str, 
                                 width: int = 512, height: int = 512) -> GenerationResult:
        """Generate image from text prompt"""
        pass
    
    @abstractmethod
    async def generate_batch(self, prompts: List[str], output_dir: str, 
                           width: int = 512, height: int = 512) -> List[GenerationResult]:
        """Generate multiple images from prompts"""
        pass

class IAudioGenerator(ABC):
    """Interface for audio generation services"""
    
    @abstractmethod
    async def text_to_speech(self, text: str, output_path: str, 
                           voice: str = "default", speed: float = 1.0) -> GenerationResult:
        """Convert text to speech"""
        pass
    
    @abstractmethod
    async def generate_silence(self, duration: float, output_path: str) -> GenerationResult:
        """Generate silence audio file"""
        pass
    
    @abstractmethod
    async def concatenate_audio(self, audio_paths: List[str], output_path: str) -> GenerationResult:
        """Concatenate multiple audio files"""
        pass

class ICLIToolChecker(ABC):
    """Interface for checking CLI tool availability"""
    
    @abstractmethod
    async def check_tool_availability(self, tool_name: str) -> bool:
        """Check if a CLI tool is available"""
        pass
    
    @abstractmethod
    async def get_tool_version(self, tool_name: str) -> Optional[str]:
        """Get version of a CLI tool"""
        pass
    
    @abstractmethod
    async def install_missing_tools(self) -> Dict[str, bool]:
        """Attempt to install missing tools"""
        pass

class BaseGenerator(ABC):
    """Base class for all generators with common functionality"""
    
    def __init__(self, output_dir: str = "/tmp/cli_generations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_output_path(self, filename: str) -> str:
        """Generate full output path"""
        return str(self.output_dir / filename)
    
    async def _run_command(self, command: List[str], timeout: int = 300) -> tuple[bool, str, str]:
        """Run CLI command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return (
                process.returncode == 0,
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore')
            )
            
        except asyncio.TimeoutError:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Command execution error: {str(e)}"
    
    def _create_generation_result(self, success: bool, file_path: Optional[str] = None, 
                                 error: Optional[str] = None, **metadata) -> GenerationResult:
        """Create standardized generation result"""
        return GenerationResult(
            success=success,
            file_path=file_path,
            error_message=error,
            metadata=metadata
        )