"""
CLI Tool Checker Service
Checks availability and versions of CLI tools
"""

import asyncio
import subprocess
import logging
from typing import Dict, Optional, List
from pathlib import Path

from .interfaces import ICLIToolChecker, BaseGenerator

logger = logging.getLogger(__name__)

class CLIToolChecker(BaseGenerator, ICLIToolChecker):
    """Service for checking CLI tool availability and installation"""
    
    def __init__(self):
        super().__init__()
        self.tool_commands = {
            # Document generation tools
            "pandoc": ["pandoc", "--version"],
            "pdflatex": ["pdflatex", "--version"],
            "xelatex": ["xelatex", "--version"],
            "lualatex": ["lualatex", "--version"],
            
            # Video generation tools
            "ffmpeg": ["ffmpeg", "-version"],
            "ffprobe": ["ffprobe", "-version"],
            
            # Audio generation tools
            "espeak": ["espeak", "--version"],
            "festival": ["festival", "--version"],
            "sox": ["sox", "--version"],
            
            # System tools
            "python": ["python", "--version"],
            "pip": ["pip", "--version"],
            "git": ["git", "--version"],
        }
        
        self.python_packages = {
            # Document packages
            "python-docx": "docx",
            "python-pptx": "pptx", 
            "openpyxl": "openpyxl",
            
            # Image generation packages
            "torch": "torch",
            "diffusers": "diffusers",
            "transformers": "transformers",
            "Pillow": "PIL",
            
            # Video generation packages
            "moviepy": "moviepy",
            "opencv-python": "cv2",
            
            # Audio generation packages
            "pyttsx3": "pyttsx3",
            "gTTS": "gtts",
            "pydub": "pydub",
            "pygame": "pygame",
        }
    
    async def check_tool_availability(self, tool_name: str) -> bool:
        """Check if a CLI tool is available"""
        try:
            if tool_name in self.tool_commands:
                command = self.tool_commands[tool_name]
                success, _, _ = await self._run_command(command, timeout=10)
                return success
            elif tool_name in self.python_packages:
                return await self._check_python_package(self.python_packages[tool_name])
            else:
                # Try generic version check
                command = [tool_name, "--version"]
                success, _, _ = await self._run_command(command, timeout=10)
                return success
                
        except Exception as e:
            logger.debug(f"Tool availability check failed for {tool_name}: {e}")
            return False
    
    async def _check_python_package(self, package_name: str) -> bool:
        """Check if a Python package is available"""
        try:
            command = ["python", "-c", f"import {package_name}"]
            success, _, _ = await self._run_command(command, timeout=10)
            return success
        except Exception:
            return False
    
    async def get_tool_version(self, tool_name: str) -> Optional[str]:
        """Get version of a CLI tool"""
        try:
            if tool_name in self.tool_commands:
                command = self.tool_commands[tool_name]
                success, stdout, stderr = await self._run_command(command, timeout=10)
                if success:
                    # Extract version from output (first line usually contains version)
                    output = stdout or stderr
                    return output.split('\n')[0].strip() if output else None
            elif tool_name in self.python_packages:
                package_import = self.python_packages[tool_name]
                command = ["python", "-c", f"import {package_import}; print(getattr({package_import}, '__version__', 'unknown'))"]
                success, stdout, _ = await self._run_command(command, timeout=10)
                if success:
                    return stdout.strip()
            else:
                # Try generic version check
                command = [tool_name, "--version"]
                success, stdout, stderr = await self._run_command(command, timeout=10)
                if success:
                    output = stdout or stderr
                    return output.split('\n')[0].strip() if output else None
                    
        except Exception as e:
            logger.debug(f"Version check failed for {tool_name}: {e}")
            
        return None
    
    async def install_missing_tools(self) -> Dict[str, bool]:
        """Attempt to install missing tools"""
        results = {}
        
        # Check and install Python packages
        for package_name, import_name in self.python_packages.items():
            available = await self._check_python_package(import_name)
            if not available:
                logger.info(f"Attempting to install {package_name}...")
                success = await self._install_python_package(package_name)
                results[package_name] = success
            else:
                results[package_name] = True
        
        # For system tools, we can't automatically install but we can suggest
        system_tools = ["pandoc", "pdflatex", "xelatex", "ffmpeg", "espeak", "festival"]
        for tool in system_tools:
            available = await self.check_tool_availability(tool)
            results[tool] = available
            if not available:
                logger.warning(f"System tool {tool} not available. Manual installation required.")
        
        return results
    
    async def _install_python_package(self, package_name: str) -> bool:
        """Install a Python package using pip"""
        try:
            command = ["pip", "install", package_name]
            success, stdout, stderr = await self._run_command(command, timeout=300)
            
            if success:
                logger.info(f"Successfully installed {package_name}")
                return True
            else:
                logger.error(f"Failed to install {package_name}: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Installation error for {package_name}: {e}")
            return False
    
    async def get_system_info(self) -> Dict[str, str]:
        """Get system information"""
        info = {}
        
        # Python version
        python_version = await self.get_tool_version("python")
        if python_version:
            info["python"] = python_version
        
        # Pip version
        pip_version = await self.get_tool_version("pip")
        if pip_version:
            info["pip"] = pip_version
        
        # System info
        try:
            import platform
            info["os"] = platform.system()
            info["architecture"] = platform.machine()
            info["platform"] = platform.platform()
        except Exception:
            pass
        
        # Available disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage("/tmp")
            info["disk_free_gb"] = f"{free // (1024**3)} GB"
        except Exception:
            pass
        
        # Check GPU availability
        try:
            import torch
            info["cuda_available"] = str(torch.cuda.is_available())
            if torch.cuda.is_available():
                info["cuda_device_count"] = str(torch.cuda.device_count())
                info["cuda_device_name"] = torch.cuda.get_device_name(0)
        except ImportError:
            info["cuda_available"] = "torch not installed"
        except Exception as e:
            info["cuda_available"] = f"error: {e}"
        
        return info
    
    async def get_comprehensive_status(self) -> Dict[str, Dict[str, str]]:
        """Get comprehensive status of all tools and system"""
        status = {
            "system_info": await self.get_system_info(),
            "cli_tools": {},
            "python_packages": {}
        }
        
        # Check CLI tools
        for tool_name in self.tool_commands.keys():
            available = await self.check_tool_availability(tool_name)
            version = await self.get_tool_version(tool_name) if available else None
            
            status["cli_tools"][tool_name] = {
                "available": str(available),
                "version": version or "unknown"
            }
        
        # Check Python packages
        for package_name, import_name in self.python_packages.items():
            available = await self._check_python_package(import_name)
            version = None
            if available:
                try:
                    command = ["python", "-c", f"import {import_name}; print(getattr({import_name}, '__version__', 'unknown'))"]
                    success, stdout, _ = await self._run_command(command, timeout=10)
                    if success:
                        version = stdout.strip()
                except Exception:
                    pass
            
            status["python_packages"][package_name] = {
                "available": str(available),
                "version": version or "unknown"
            }
        
        return status
    
    async def get_installation_suggestions(self) -> Dict[str, List[str]]:
        """Get installation suggestions for missing tools"""
        suggestions = {
            "python_packages": [],
            "system_packages": []
        }
        
        # Check Python packages
        for package_name, import_name in self.python_packages.items():
            available = await self._check_python_package(import_name)
            if not available:
                suggestions["python_packages"].append(f"pip install {package_name}")
        
        # Check system tools
        system_installs = {
            "pandoc": {
                "ubuntu": "sudo apt-get install pandoc",
                "macOS": "brew install pandoc",
                "windows": "Download from https://pandoc.org/installing.html"
            },
            "pdflatex": {
                "ubuntu": "sudo apt-get install texlive-latex-base texlive-latex-extra",
                "macOS": "brew install --cask mactex",
                "windows": "Download MiKTeX from https://miktex.org/"
            },
            "ffmpeg": {
                "ubuntu": "sudo apt-get install ffmpeg",
                "macOS": "brew install ffmpeg",
                "windows": "Download from https://ffmpeg.org/"
            },
            "espeak": {
                "ubuntu": "sudo apt-get install espeak",
                "macOS": "brew install espeak",
                "windows": "Download from http://espeak.sourceforge.net/download.html"
            },
            "festival": {
                "ubuntu": "sudo apt-get install festival",
                "macOS": "brew install festival",
                "windows": "Manual compilation required"
            }
        }
        
        for tool_name, installs in system_installs.items():
            available = await self.check_tool_availability(tool_name)
            if not available:
                suggestions["system_packages"].extend([
                    f"{tool_name}:",
                    f"  Ubuntu: {installs['ubuntu']}",
                    f"  macOS: {installs['macOS']}",
                    f"  Windows: {installs['windows']}"
                ])
        
        return suggestions