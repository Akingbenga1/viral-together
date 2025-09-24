"""
Video Generation Service
Implements video creation using FFMPEG and moviepy
"""

import asyncio
import tempfile
from typing import List, Optional
from pathlib import Path
import logging
import json

from .interfaces import IVideoGenerator, BaseGenerator, GenerationResult

logger = logging.getLogger(__name__)

class VideoGenerationService(BaseGenerator, IVideoGenerator):
    """Service for generating videos using FFMPEG and moviepy"""
    
    def __init__(self, output_dir: str = "/tmp/cli_generations/videos"):
        super().__init__(output_dir)
        self.required_tools = ["ffmpeg", "ffprobe"]
    
    async def create_video_from_images(self, image_paths: List[str], output_path: str, 
                                     duration_per_image: float = 2.0) -> GenerationResult:
        """Create video from sequence of images using FFMPEG"""
        try:
            if not output_path.endswith(('.mp4', '.avi', '.mov')):
                output_path += '.mp4'
            
            full_path = self._get_output_path(output_path)
            
            # Check if all image files exist
            for img_path in image_paths:
                if not Path(img_path).exists():
                    return self._create_generation_result(
                        success=False,
                        error=f"Image file not found: {img_path}"
                    )
            
            # Create a temporary text file with image list for FFMPEG
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_list:
                for img_path in image_paths:
                    temp_list.write(f"file '{img_path}'\n")
                    temp_list.write(f"duration {duration_per_image}\n")
                temp_list_path = temp_list.name
            
            # Use FFMPEG to create video from images
            command = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-f", "concat",
                "-safe", "0",
                "-i", temp_list_path,
                "-vf", "scale=1280:720,fps=30",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=600)
            
            # Clean up temporary file
            Path(temp_list_path).unlink()
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="mp4",
                    images_count=len(image_paths),
                    duration=duration_per_image * len(image_paths)
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Video from images generation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def add_audio_to_video(self, video_path: str, audio_path: str, output_path: str) -> GenerationResult:
        """Add audio track to video using FFMPEG"""
        try:
            if not output_path.endswith(('.mp4', '.avi', '.mov')):
                output_path += '.mp4'
            
            full_path = self._get_output_path(output_path)
            
            # Check if input files exist
            if not Path(video_path).exists():
                return self._create_generation_result(
                    success=False,
                    error=f"Video file not found: {video_path}"
                )
            
            if not Path(audio_path).exists():
                return self._create_generation_result(
                    success=False,
                    error=f"Audio file not found: {audio_path}"
                )
            
            # Use FFMPEG to combine video and audio
            command = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",  # Copy video stream
                "-c:a", "aac",   # Encode audio as AAC
                "-strict", "experimental",
                "-shortest",     # Match shortest stream
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=600)
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="mp4",
                    video_source=video_path,
                    audio_source=audio_path
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Add audio to video error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def create_text_video(self, text: str, output_path: str, 
                              duration: float = 5.0, font_size: int = 48) -> GenerationResult:
        """Create video with text overlay using FFMPEG"""
        try:
            if not output_path.endswith(('.mp4', '.avi', '.mov')):
                output_path += '.mp4'
            
            full_path = self._get_output_path(output_path)
            
            # Escape text for FFMPEG
            escaped_text = text.replace("'", "\\'").replace(":", "\\:")
            
            # Create video with text overlay
            command = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-f", "lavfi",
                "-i", f"color=c=black:s=1280x720:d={duration}",
                "-vf", f"drawtext=text='{escaped_text}':fontcolor=white:fontsize={font_size}:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=300)
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="mp4",
                    text_content=text,
                    duration=duration,
                    font_size=font_size
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Text video generation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def concatenate_videos(self, video_paths: List[str], output_path: str) -> GenerationResult:
        """Concatenate multiple videos using FFMPEG"""
        try:
            if not output_path.endswith(('.mp4', '.avi', '.mov')):
                output_path += '.mp4'
            
            full_path = self._get_output_path(output_path)
            
            # Check if all video files exist
            for video_path in video_paths:
                if not Path(video_path).exists():
                    return self._create_generation_result(
                        success=False,
                        error=f"Video file not found: {video_path}"
                    )
            
            # Create temporary text file with video list
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_list:
                for video_path in video_paths:
                    temp_list.write(f"file '{video_path}'\n")
                temp_list_path = temp_list.name
            
            # Use FFMPEG to concatenate videos
            command = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-f", "concat",
                "-safe", "0",
                "-i", temp_list_path,
                "-c", "copy",  # Copy streams without re-encoding
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=900)
            
            # Clean up temporary file
            Path(temp_list_path).unlink()
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="mp4",
                    input_videos=len(video_paths),
                    sources=video_paths
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Video concatenation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def resize_video(self, input_path: str, output_path: str, width: int, height: int) -> GenerationResult:
        """Resize video to specified dimensions using FFMPEG"""
        try:
            if not output_path.endswith(('.mp4', '.avi', '.mov')):
                output_path += '.mp4'
            
            full_path = self._get_output_path(output_path)
            
            # Check if input file exists
            if not Path(input_path).exists():
                return self._create_generation_result(
                    success=False,
                    error=f"Input video file not found: {input_path}"
                )
            
            # Use FFMPEG to resize video
            command = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-i", input_path,
                "-vf", f"scale={width}:{height}",
                "-c:v", "libx264",
                "-c:a", "copy",  # Copy audio stream
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=600)
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="mp4",
                    original_file=input_path,
                    new_dimensions=f"{width}x{height}"
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Video resize error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def create_slideshow_video(self, slides_data: List[dict], output_path: str) -> GenerationResult:
        """Create slideshow video using moviepy (fallback implementation)"""
        try:
            # Try to use moviepy if available
            try:
                from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips
                from moviepy.video.fx import resize
            except ImportError:
                return self._create_generation_result(
                    success=False,
                    error="moviepy package not installed. Install with: pip install moviepy"
                )
            
            if not output_path.endswith(('.mp4', '.avi', '.mov')):
                output_path += '.mp4'
            
            full_path = self._get_output_path(output_path)
            
            clips = []
            for slide in slides_data:
                # Create text clip for each slide
                text = slide.get('text', 'Slide')
                duration = slide.get('duration', 3.0)
                
                txt_clip = TextClip(
                    text,
                    fontsize=50,
                    color='white',
                    size=(1280, 720)
                ).set_duration(duration).set_position('center')
                
                # Create background
                bg_clip = TextClip(
                    '',
                    size=(1280, 720),
                    color=(0, 0, 0)
                ).set_duration(duration)
                
                # Composite
                slide_clip = CompositeVideoClip([bg_clip, txt_clip])
                clips.append(slide_clip)
            
            # Concatenate all slides
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Write video file
            final_clip.write_videofile(
                full_path,
                fps=24,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Clean up
            final_clip.close()
            for clip in clips:
                clip.close()
            
            return self._create_generation_result(
                success=True,
                file_path=full_path,
                format="mp4",
                slides_count=len(slides_data),
                engine="moviepy"
            )
            
        except Exception as e:
            logger.error(f"Slideshow video generation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )