"""
Audio Generation Service
Implements audio generation using text-to-speech and audio manipulation
"""

import asyncio
import tempfile
import logging
from typing import List, Optional
from pathlib import Path
import uuid

from .interfaces import IAudioGenerator, BaseGenerator, GenerationResult

logger = logging.getLogger(__name__)

class AudioGenerationService(BaseGenerator, IAudioGenerator):
    """Service for generating audio using TTS and audio manipulation"""
    
    def __init__(self, output_dir: str = "/tmp/cli_generations/audio"):
        super().__init__(output_dir)
        # Try to use imageio-ffmpeg binary if available
        try:
            import imageio_ffmpeg
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            logger.info(f"Using imageio-ffmpeg binary: {self.ffmpeg_path}")
        except ImportError:
            self.ffmpeg_path = "ffmpeg"  # Fallback to system ffmpeg
    
    async def text_to_speech(self, text: str, output_path: str, 
                           voice: str = "default", speed: float = 1.0) -> GenerationResult:
        """Convert text to speech using available TTS engines"""
        try:
            if not output_path.endswith(('.mp3', '.wav', '.flac')):
                output_path += '.wav'
            
            full_path = self._get_output_path(output_path)
            
            # Try different TTS engines in order of preference
            engines = [
                ("pyttsx3", self._generate_with_pyttsx3),
                ("gtts", self._generate_with_gtts),
                ("espeak", self._generate_with_espeak),
                ("festival", self._generate_with_festival)
            ]
            
            for engine_name, generator_func in engines:
                try:
                    result = await generator_func(text, full_path, voice, speed)
                    if result.success:
                        result.metadata["engine"] = engine_name
                        return result
                except Exception as e:
                    logger.warning(f"TTS engine {engine_name} failed: {e}")
                    continue
            
            return self._create_generation_result(
                success=False,
                error="No TTS engines available. Install: pip install pyttsx3 gTTS or system packages espeak/festival"
            )
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def _generate_with_pyttsx3(self, text: str, output_path: str, voice: str, speed: float) -> GenerationResult:
        """Generate speech using pyttsx3 (offline)"""
        try:
            import pyttsx3
        except ImportError:
            raise ImportError("pyttsx3 not available")
        
        def generate_speech():
            engine = pyttsx3.init()
            
            # Set voice if specified
            if voice != "default":
                voices = engine.getProperty('voices')
                for v in voices:
                    if voice.lower() in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break
            
            # Set speed
            rate = engine.getProperty('rate')
            engine.setProperty('rate', int(rate * speed))
            
            # Generate speech
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            engine.stop()
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, generate_speech)
        
        if Path(output_path).exists():
            return self._create_generation_result(
                success=True,
                file_path=output_path,
                format="wav",
                text=text,
                voice=voice,
                speed=speed
            )
        else:
            raise Exception("Failed to generate speech file")
    
    async def _generate_with_gtts(self, text: str, output_path: str, voice: str, speed: float) -> GenerationResult:
        """Generate speech using gTTS (requires internet)"""
        try:
            from gtts import gTTS
            import pygame
        except ImportError:
            raise ImportError("gTTS or pygame not available")
        
        def generate_speech():
            # Map voice to language
            lang_map = {
                "english": "en",
                "spanish": "es", 
                "french": "fr",
                "german": "de",
                "italian": "it",
                "default": "en"
            }
            lang = lang_map.get(voice.lower(), "en")
            
            tts = gTTS(text=text, lang=lang, slow=(speed < 1.0))
            
            # gTTS generates MP3, convert to requested format if needed
            if output_path.endswith('.wav'):
                temp_mp3 = output_path.replace('.wav', '_temp.mp3')
                tts.save(temp_mp3)
                
                # Convert MP3 to WAV using pygame/pydub
                try:
                    import pydub
                    audio = pydub.AudioSegment.from_mp3(temp_mp3)
                    audio.export(output_path, format="wav")
                    Path(temp_mp3).unlink()
                except ImportError:
                    # Fallback: just rename mp3 to wav (not ideal but works)
                    Path(temp_mp3).rename(output_path)
            else:
                tts.save(output_path)
        
        # Run in executor
        loop = asyncio.get_event_loop()
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, generate_speech)
        
        if Path(output_path).exists():
            return self._create_generation_result(
                success=True,
                file_path=output_path,
                format="mp3" if output_path.endswith('.mp3') else "wav",
                text=text,
                voice=voice,
                speed=speed
            )
        else:
            raise Exception("Failed to generate speech file")
    
    async def _generate_with_espeak(self, text: str, output_path: str, voice: str, speed: float) -> GenerationResult:
        """Generate speech using espeak CLI tool"""
        # Check if espeak is available
        check_cmd = ["espeak", "--version"]
        available, _, _ = await self._run_command(check_cmd, timeout=10)
        
        if not available:
            raise Exception("espeak not available")
        
        # Generate speech using espeak
        wpm = int(175 * speed)  # words per minute
        command = [
            "espeak",
            "-w", output_path,
            "-s", str(wpm),
            text
        ]
        
        if voice != "default":
            command.extend(["-v", voice])
        
        success, stdout, stderr = await self._run_command(command, timeout=60)
        
        if success and Path(output_path).exists():
            return self._create_generation_result(
                success=True,
                file_path=output_path,
                format="wav",
                text=text,
                voice=voice,
                speed=speed
            )
        else:
            raise Exception(f"espeak failed: {stderr}")
    
    async def _generate_with_festival(self, text: str, output_path: str, voice: str, speed: float) -> GenerationResult:
        """Generate speech using festival CLI tool"""
        # Check if festival is available
        check_cmd = ["festival", "--version"]
        available, _, _ = await self._run_command(check_cmd, timeout=10)
        
        if not available:
            raise Exception("festival not available")
        
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_text:
            temp_text.write(text)
            temp_text_path = temp_text.name
        
        # Generate speech using festival
        command = [
            "festival",
            "--tts",
            temp_text_path,
            "--otype", "wav",
            "-o", output_path
        ]
        
        success, stdout, stderr = await self._run_command(command, timeout=120)
        
        # Clean up temporary file
        Path(temp_text_path).unlink()
        
        if success and Path(output_path).exists():
            return self._create_generation_result(
                success=True,
                file_path=output_path,
                format="wav",
                text=text,
                voice=voice,
                speed=speed
            )
        else:
            raise Exception(f"festival failed: {stderr}")
    
    async def generate_silence(self, duration: float, output_path: str) -> GenerationResult:
        """Generate silence audio file using FFMPEG"""
        try:
            if not output_path.endswith(('.mp3', '.wav', '.flac')):
                output_path += '.wav'
            
            full_path = self._get_output_path(output_path)
            
            # Use FFMPEG to generate silence
            command = [
                self.ffmpeg_path,
                "-y",  # Overwrite output
                "-f", "lavfi",
                "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", str(duration),
                "-c:a", "pcm_s16le",
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=60)
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="wav",
                    duration=duration,
                    type="silence"
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Silence generation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def concatenate_audio(self, audio_paths: List[str], output_path: str) -> GenerationResult:
        """Concatenate multiple audio files using FFMPEG"""
        try:
            if not output_path.endswith(('.mp3', '.wav', '.flac')):
                output_path += '.wav'
            
            full_path = self._get_output_path(output_path)
            
            # Check if all audio files exist
            for audio_path in audio_paths:
                if not Path(audio_path).exists():
                    return self._create_generation_result(
                        success=False,
                        error=f"Audio file not found: {audio_path}"
                    )
            
            # Create temporary file list for FFMPEG
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_list:
                for audio_path in audio_paths:
                    temp_list.write(f"file '{audio_path}'\n")
                temp_list_path = temp_list.name
            
            # Use FFMPEG to concatenate audio files
            command = [
                self.ffmpeg_path,
                "-y",  # Overwrite output
                "-f", "concat",
                "-safe", "0",
                "-i", temp_list_path,
                "-c", "copy",  # Copy without re-encoding
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=300)
            
            # Clean up temporary file
            Path(temp_list_path).unlink()
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="wav",
                    input_files=len(audio_paths),
                    sources=audio_paths
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Audio concatenation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def adjust_audio_speed(self, input_path: str, output_path: str, speed: float) -> GenerationResult:
        """Adjust audio playback speed using FFMPEG"""
        try:
            if not output_path.endswith(('.mp3', '.wav', '.flac')):
                output_path += '.wav'
            
            full_path = self._get_output_path(output_path)
            
            # Check if input file exists
            if not Path(input_path).exists():
                return self._create_generation_result(
                    success=False,
                    error=f"Input audio file not found: {input_path}"
                )
            
            # Use FFMPEG to adjust speed
            command = [
                self.ffmpeg_path,
                "-y",  # Overwrite output
                "-i", input_path,
                "-filter:a", f"atempo={speed}",
                full_path
            ]
            
            success, stdout, stderr = await self._run_command(command, timeout=300)
            
            if success and Path(full_path).exists():
                return self._create_generation_result(
                    success=True,
                    file_path=full_path,
                    format="wav",
                    original_file=input_path,
                    speed_multiplier=speed
                )
            else:
                return self._create_generation_result(
                    success=False,
                    error=f"FFMPEG error: {stderr}"
                )
                
        except Exception as e:
            logger.error(f"Audio speed adjustment error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )