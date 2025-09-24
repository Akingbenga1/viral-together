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
        """Generate image from text prompt using Stable Diffusion or fallback methods"""
        try:
            if not output_path.endswith(('.png', '.jpg', '.jpeg')):
                output_path += '.png'
            
            full_path = self._get_output_path(output_path)
            
            # Try Stable Diffusion first
            try:
                pipeline = await self._initialize_pipeline()
                
                # Generate image with Stable Diffusion
                logger.info(f"Generating image with Stable Diffusion: {prompt}")
                
                def generate_image():
                    with torch.no_grad():
                        result = pipeline(
                            prompt,
                            width=width,
                            height=height,
                            num_inference_steps=20,
                            guidance_scale=7.5,
                            generator=torch.Generator(device=self._device).manual_seed(42)
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
                    device=self._device,
                    engine="stable_diffusion"
                )
                
            except ImportError:
                # Fallback to PIL-based image generation
                logger.info("Stable Diffusion not available, using PIL fallback")
                return await self._generate_with_pil_fallback(prompt, full_path, width, height)
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            # Try PIL fallback as last resort
            try:
                return await self._generate_with_pil_fallback(prompt, full_path, width, height)
            except Exception as fallback_error:
                return self._create_generation_result(
                    success=False,
                    error=f"All image generation methods failed. Stable Diffusion: {str(e)}, PIL fallback: {str(fallback_error)}"
                )
    
    async def _generate_with_pil_fallback(self, prompt: str, output_path: str, 
                                        width: int, height: int) -> GenerationResult:
        """Generate image using PIL and other free Python packages"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            import hashlib
            
            # Create base image
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Generate colors based on prompt hash for consistency
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
            random.seed(int(prompt_hash[:8], 16))
            
            # Create gradient background based on prompt
            for y in range(height):
                r = int(150 + (y / height) * 105)
                g = int(180 + (y / height) * 75) 
                b = int(200 + (y / height) * 55)
                color = (r, g, b)
                draw.line([(0, y), (width, y)], fill=color)
            
            # Add geometric shapes based on prompt keywords
            self._add_prompt_based_shapes(draw, prompt, width, height)
            
            # Add text overlay
            self._add_text_overlay(draw, prompt, width, height)
            
            # Save image
            image.save(output_path, 'PNG')
            
            return self._create_generation_result(
                success=True,
                file_path=output_path,
                format="png",
                prompt=prompt,
                dimensions=f"{width}x{height}",
                engine="pil_fallback"
            )
            
        except ImportError:
            return self._create_generation_result(
                success=False,
                error="PIL (Pillow) not available. Install with: pip install Pillow"
            )
    
    def _add_prompt_based_shapes(self, draw, prompt: str, width: int, height: int):
        """Add shapes based on prompt keywords"""
        prompt_lower = prompt.lower()
        
        # Color mapping for different themes
        if any(word in prompt_lower for word in ['business', 'professional', 'corporate']):
            colors = [(70, 130, 180), (100, 149, 237), (135, 206, 235)]  # Blues
        elif any(word in prompt_lower for word in ['creative', 'art', 'design']):
            colors = [(255, 182, 193), (255, 160, 122), (255, 192, 203)]  # Pastels
        elif any(word in prompt_lower for word in ['technology', 'digital', 'tech']):
            colors = [(0, 255, 127), (60, 179, 113), (46, 139, 87)]  # Greens
        elif any(word in prompt_lower for word in ['marketing', 'influencer', 'social']):
            colors = [(255, 105, 180), (255, 20, 147), (219, 112, 147)]  # Pinks
        else:
            colors = [(128, 128, 128), (169, 169, 169), (192, 192, 192)]  # Grays
        
        # Add circles for 'influencer', 'social', 'community'
        if any(word in prompt_lower for word in ['influencer', 'social', 'community']):
            for i in range(3):
                x = width // 4 + (i * width // 4)
                y = height // 3
                radius = 30 + (i * 10)
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                           fill=colors[i % len(colors)], outline='white', width=2)
        
        # Add rectangles for 'business', 'professional'
        if any(word in prompt_lower for word in ['business', 'professional', 'corporate']):
            for i in range(2):
                x1 = width // 6 + (i * width // 3)
                y1 = height // 2
                x2 = x1 + 80
                y2 = y1 + 60
                draw.rectangle([x1, y1, x2, y2], 
                             fill=colors[i % len(colors)], outline='white', width=2)
        
        # Add triangles for 'growth', 'trending'
        if any(word in prompt_lower for word in ['growth', 'trending', 'success']):
            points = [(width//2, height//4), (width//2-40, height//2), (width//2+40, height//2)]
            draw.polygon(points, fill=colors[0], outline='white', width=2)
    
    def _add_text_overlay(self, draw, prompt: str, width: int, height: int):
        """Add text overlay to the image"""
        try:
            # Try to use a larger font if available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
            
            # Truncate prompt if too long
            display_text = prompt[:50] + "..." if len(prompt) > 50 else prompt
            
            # Calculate text position
            if font:
                bbox = draw.textbbox((0, 0), display_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(display_text) * 6
                text_height = 11
            
            x = (width - text_width) // 2
            y = height - 60
            
            # Add semi-transparent background for text
            padding = 10
            draw.rectangle([x-padding, y-padding, x+text_width+padding, y+text_height+padding], 
                         fill=(0, 0, 0, 128))
            
            # Draw text
            draw.text((x, y), display_text, fill='white', font=font)
            
        except Exception as e:
            logger.warning(f"Text overlay failed: {e}")
    
    async def generate_chart_image(self, data: dict, chart_type: str, output_path: str, 
                                 width: int = 800, height: int = 600) -> GenerationResult:
        """Generate chart/graph images using matplotlib"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            if not output_path.endswith(('.png', '.jpg', '.jpeg')):
                output_path += '.png'
            
            full_path = self._get_output_path(output_path)
            
            # Set figure size
            fig, ax = plt.subplots(figsize=(width/100, height/100))
            
            if chart_type == 'bar':
                ax.bar(data.get('labels', []), data.get('values', []))
                ax.set_title(data.get('title', 'Bar Chart'))
            elif chart_type == 'line':
                ax.plot(data.get('x', []), data.get('y', []))
                ax.set_title(data.get('title', 'Line Chart'))
            elif chart_type == 'pie':
                ax.pie(data.get('values', []), labels=data.get('labels', []), autopct='%1.1f%%')
                ax.set_title(data.get('title', 'Pie Chart'))
            else:
                # Default bar chart
                ax.bar(data.get('labels', ['A', 'B', 'C']), data.get('values', [1, 2, 3]))
                ax.set_title(data.get('title', 'Chart'))
            
            # Save the chart
            plt.savefig(full_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            return self._create_generation_result(
                success=True,
                file_path=full_path,
                format="png",
                chart_type=chart_type,
                dimensions=f"{width}x{height}",
                engine="matplotlib"
            )
            
        except ImportError:
            return self._create_generation_result(
                success=False,
                error="matplotlib not available. Install with: pip install matplotlib"
            )
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return self._create_generation_result(
                success=False,
                error=str(e)
            )
    
    async def generate_logo_style_image(self, text: str, output_path: str, 
                                      width: int = 400, height: int = 200) -> GenerationResult:
        """Generate logo-style images with text and shapes"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import math
            
            if not output_path.endswith(('.png', '.jpg', '.jpeg')):
                output_path += '.png'
            
            full_path = self._get_output_path(output_path)
            
            # Create image with transparent background
            image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            
            # Add gradient background
            for y in range(height):
                alpha = int(255 * (1 - y / height) * 0.3)
                color = (100, 150, 255, alpha)
                draw.line([(0, y), (width, y)], fill=color)
            
            # Add decorative elements
            center_x, center_y = width // 2, height // 2
            
            # Add circles around the text
            for radius in [60, 80, 100]:
                draw.ellipse([center_x - radius, center_y - radius, 
                            center_x + radius, center_y + radius], 
                           outline=(100, 150, 255, 100), width=2)
            
            # Add text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            except:
                font = None
            
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(text) * 12
                text_height = 16
            
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
            
            # Draw text with shadow
            draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 128), font=font)
            draw.text((text_x, text_y), text, fill=(50, 50, 150, 255), font=font)
            
            # Save image
            image.save(full_path, 'PNG')
            
            return self._create_generation_result(
                success=True,
                file_path=full_path,
                format="png",
                text=text,
                dimensions=f"{width}x{height}",
                engine="pil_logo"
            )
            
        except Exception as e:
            logger.error(f"Logo generation error: {e}")
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