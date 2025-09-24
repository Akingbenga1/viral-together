"""
Image Generation Service
Implements image generation using Stable Diffusion
"""

import asyncio
import logging
from typing import List, Optional
from pathlib import Path
import uuid

from .interfaces import IImageGenerator, BaseGenerator, GenerationResult

logger = logging.getLogger(__name__)

class ImageGenerationService(BaseGenerator, IImageGenerator):
    """Service for generating images using Stable Diffusion"""
    
    def __init__(self, output_dir: str = "/tmp/cli_generations/images"):
        super().__init__(output_dir)
        self._pipeline = None
        self._device = None
    
    async def _initialize_pipeline(self):
        """Initialize Stable Diffusion pipeline lazily"""
        if self._pipeline is not None:
            return self._pipeline
        
        try:
            # Import here to handle missing dependencies gracefully
            try:
                import torch
                from diffusers import StableDiffusionPipeline
                import warnings
                warnings.filterwarnings("ignore", category=FutureWarning)
            except ImportError as e:
                missing_deps = []
                if "torch" in str(e):
                    missing_deps.append("torch")
                if "diffusers" in str(e):
                    missing_deps.append("diffusers")
                if "transformers" in str(e):
                    missing_deps.append("transformers")
                    
                error_msg = f"Missing dependencies: {', '.join(missing_deps)}. Install with: pip install torch diffusers transformers"
                logger.error(error_msg)
                raise ImportError(error_msg)
            
            # Determine device
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self._device}")
            
            # Load the pipeline
            logger.info("Loading Stable Diffusion pipeline...")
            self._pipeline = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
                safety_checker=None,  # Disable safety checker for faster inference
                requires_safety_checker=False
            )
            
            self._pipeline = self._pipeline.to(self._device)
            
            # Enable memory efficient attention if available
            if hasattr(self._pipeline, "enable_memory_efficient_attention"):
                self._pipeline.enable_memory_efficient_attention()
            
            # Enable attention slicing for lower VRAM usage
            if hasattr(self._pipeline, "enable_attention_slicing"):
                self._pipeline.enable_attention_slicing()
            
            logger.info("Stable Diffusion pipeline loaded successfully")
            return self._pipeline
            
        except Exception as e:
            logger.error(f"Failed to initialize Stable Diffusion pipeline: {e}")
            raise e
    
    async def generate_from_prompt(self, prompt: str, output_path: str, 
                                 width: int = 512, height: int = 512) -> GenerationResult:
        """Generate image from text prompt using Stable Diffusion"""
        try:
            if not output_path.endswith(('.png', '.jpg', '.jpeg')):
                output_path += '.png'
            
            full_path = self._get_output_path(output_path)
            
            # Initialize pipeline
            pipeline = await self._initialize_pipeline()
            
            # Generate image
            logger.info(f"Generating image with prompt: {prompt}")
            
            # Run inference in a thread to avoid blocking
            def generate_image():
                with torch.no_grad():
                    result = pipeline(
                        prompt,
                        width=width,
                        height=height,
                        num_inference_steps=20,  # Faster generation with fewer steps
                        guidance_scale=7.5,
                        generator=torch.Generator(device=self._device).manual_seed(42)  # For reproducible results
                    )
                    return result.images[0]
            
            # Run generation in executor to avoid blocking
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                image = await loop.run_in_executor(executor, generate_image)
            
            # Save image
            image.save(full_path)
            
            return self._create_generation_result(
                success=True,
                file_path=full_path,
                format="png",
                prompt=prompt,
                dimensions=f"{width}x{height}",
                device=self._device
            )
            
        except ImportError as e:
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def generate_batch(self, prompts: List[str], output_dir: str, 
                           width: int = 512, height: int = 512) -> List[GenerationResult]:
        """Generate multiple images from prompts"""
        results = []
        
        try:
            # Initialize pipeline once for all generations
            pipeline = await self._initialize_pipeline()
            
            for i, prompt in enumerate(prompts):
                filename = f"batch_image_{i}_{uuid.uuid4().hex[:8]}.png"
                output_path = Path(output_dir) / filename
                
                result = await self.generate_from_prompt(
                    prompt=prompt,
                    output_path=str(output_path),
                    width=width,
                    height=height
                )
                
                results.append(result)
                
                # Log progress
                logger.info(f"Generated batch image {i+1}/{len(prompts)}")
            
        except Exception as e:
            logger.error(f"Batch generation error: {e}")
            # Add error result for remaining prompts
            error_result = self._create_generation_result(
                success=False,
                error=str(e)
            )
            results.extend([error_result] * (len(prompts) - len(results)))
        
        return results
    
    async def generate_variations(self, base_prompt: str, variations: List[str], 
                                output_dir: str, width: int = 512, height: int = 512) -> List[GenerationResult]:
        """Generate variations of a base prompt"""
        full_prompts = [f"{base_prompt}, {variation}" for variation in variations]
        return await self.generate_batch(full_prompts, output_dir, width, height)
    
    async def generate_with_negative_prompt(self, prompt: str, negative_prompt: str, 
                                          output_path: str, width: int = 512, height: int = 512) -> GenerationResult:
        """Generate image with negative prompt for better quality"""
        try:
            if not output_path.endswith(('.png', '.jpg', '.jpeg')):
                output_path += '.png'
            
            full_path = self._get_output_path(output_path)
            
            # Initialize pipeline
            pipeline = await self._initialize_pipeline()
            
            # Generate image with negative prompt
            logger.info(f"Generating image with prompt: {prompt}, negative: {negative_prompt}")
            
            def generate_image():
                with torch.no_grad():
                    result = pipeline(
                        prompt,
                        negative_prompt=negative_prompt,
                        width=width,
                        height=height,
                        num_inference_steps=25,  # More steps for better quality
                        guidance_scale=8.0,  # Higher guidance for better adherence
                        generator=torch.Generator(device=self._device).manual_seed(42)
                    )
                    return result.images[0]
            
            # Run generation in executor
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                image = await loop.run_in_executor(executor, generate_image)
            
            # Save image
            image.save(full_path)
            
            return self._create_generation_result(
                success=True,
                file_path=full_path,
                format="png",
                prompt=prompt,
                negative_prompt=negative_prompt,
                dimensions=f"{width}x{height}",
                device=self._device
            )
            
        except ImportError as e:
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Image generation with negative prompt error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    def cleanup(self):
        """Cleanup resources"""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            
            # Clear CUDA cache if using GPU
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            logger.info("Stable Diffusion pipeline cleaned up")