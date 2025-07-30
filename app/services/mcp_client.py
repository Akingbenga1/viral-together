import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import uuid
import os
import time
import traceback

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """Lightweight MCP client for tool calling"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        self.config_file = config_file
        self.servers = {}
        self._load_config()
    
    def _load_config(self):
        """Load MCP server configurations"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.servers = config.get('servers', {})
                    logger.info(f"✅ MCP_CONFIG_LOADED: {len(self.servers)} servers configured")
            else:
                logger.warning(f"⚠️ MCP_CONFIG_MISSING: {self.config_file} not found")
                self.servers = {}
        except Exception as e:
            logger.error(f"❌ MCP_CONFIG_ERROR: Failed to load config: {str(e)}")
            self.servers = {}
    
    async def call_tool(self, server: str, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        start_time = asyncio.get_event_loop().time()
        call_id = str(uuid.uuid4())[:8]
        
        logger.info(f"🔧 MCP_CALL_START: call_id={call_id}, server={server}, tool={tool}")
        logger.debug(f"🔧 MCP_ARGS: call_id={call_id}, args={arguments}")
        
        try:
            if server not in self.servers:
                raise ValueError(f"Server '{server}' not configured")
            
            server_config = self.servers[server]
            result = await self._execute_mcp_call(server_config, tool, arguments, call_id)
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ MCP_CALL_SUCCESS: call_id={call_id}, duration={duration:.3f}s")
            logger.debug(f"🔧 MCP_RESULT: call_id={call_id}, result={result}")
            
            return result
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ MCP_CALL_FAILURE: call_id={call_id}, duration={duration:.3f}s, error={str(e)}")
            raise
    
    async def _execute_mcp_call(self, server_config: Dict, tool: str, arguments: Dict, call_id: str) -> Dict[str, Any]:
        """Execute MCP tool call via subprocess using asyncio.to_thread (Windows-compatible) with enhanced stderr handling"""
        try:
            command = server_config.get('command')
            args = server_config.get('args', [])
            env = server_config.get('env', {})
            
            # Build the full command
            full_command = [command] + args
            
            # Create MCP request payload
            mcp_request = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": arguments
                }
            }
            
            logger.debug(f"🔧 MCP_SUBPROCESS: call_id={call_id}, command={full_command}")
            
            # Prepare environment variables
            process_env = {**os.environ}
            if env:
                process_env.update(env)
            
            # Convert request to bytes (add newline for proper MCP communication)
            request_json = json.dumps(mcp_request)
            request_data = (request_json + "\n")
            
            # LOG THE EXACT REQUEST BEING SENT
            logger.info(f"📤 MCP_REQUEST_SENDING: call_id={call_id}")
            logger.debug(f"📤 MCP_REQUEST_JSON: {request_json}")
            logger.debug(f"📤 MCP_REQUEST_DATA: {len(request_data)} chars")
            
            # Use asyncio.to_thread for Windows compatibility instead of create_subprocess_exec
            logger.debug(f"🔧 MCP_THREAD_EXEC: Using asyncio.to_thread for Windows compatibility")
            
            result = await asyncio.to_thread(
                subprocess.run,
                full_command,
                input=request_data,
                capture_output=True,
                text=True,
                env=process_env,
                timeout=30  # 30 second timeout
            )

            logger.debug(f"🔧 MCP_SUBPROCESS_RESULT: {result}")
            
            # 🔍 LOG SUBPROCESS OUTPUT FOR DEBUGGING
            stdout_content = result.stdout if result.stdout else ""
            stderr_content = result.stderr if result.stderr else ""
            
            logger.debug(f"🔧 MCP_SUBPROCESS_RESULT: call_id={call_id}")
            logger.debug(f"🔧 MCP_RETURNCODE: {result.returncode}")
            logger.debug(f"🔧 MCP_STDOUT_LENGTH: {len(stdout_content)} chars")
            logger.debug(f"🔧 MCP_STDERR_LENGTH: {len(stderr_content)} chars")
            
            if stdout_content:
                logger.debug(f"🔧 MCP_STDOUT_CONTENT: {stdout_content[:500]}...")  # First 500 chars
            
            # Enhanced stderr handling - treat MCP server initialization as success
            if stderr_content:
                if "Twitter MCP server running on stdio" in stderr_content:
                    logger.info(f"✅ MCP_SERVER_READY: Twitter MCP server initialized successfully")
                    logger.debug(f"🐦 MCP_SERVER_STATUS: {stderr_content}")
                else:
                    logger.info(f"⚠️ MCP_STDERR_CONTENT: {stderr_content}")  # Show other stderr as warning
            
            if result.returncode != 0:
                error_msg = stderr_content if stderr_content else "Unknown error"
                logger.error(f"❌ MCP_PROCESS_FAILED: returncode={result.returncode}, error={error_msg}")
                raise Exception(f"MCP server returned code {result.returncode}: {error_msg}")
            
            # Check if we have any output at all
            if not stdout_content and not stderr_content:
                logger.error(f"❌ MCP_NO_OUTPUT: Neither stdout nor stderr received from MCP server")
                raise Exception("No output received from MCP server (neither stdout nor stderr)")
            
            # If we have stderr but no stdout, that might be the issue
            if not stdout_content and stderr_content:
                logger.warning(f"⚠️ MCP_STDOUT_EMPTY: Only stderr received, no stdout")
                logger.warning(f"⚠️ MCP_STDERR_DETAILS: {stderr_content}")
                raise Exception(f"MCP server sent no stdout output. stderr: {stderr_content}")
            
            # Parse response
            if not stdout_content:
                raise Exception("No stdout received from MCP server")
                
            response = json.loads(stdout_content)

            logger.debug(f"🔧 MCP_RESPONSE_UNPACK_JSON: {response}")
            
            if 'error' in response:
                raise Exception(f"MCP server error: {response['error']}")
            
            return response.get('result', {})
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ MCP_TIMEOUT: call_id={call_id}, command timed out after 30 seconds")
            raise Exception("MCP server call timed out")
        except json.JSONDecodeError as e:
            logger.error(f"❌ MCP_JSON_ERROR: call_id={call_id}, error={str(e)}")
            raise Exception(f"Invalid JSON response from MCP server: {str(e)}")
        except Exception as e:
            logger.error(f"❌ MCP_SUBPROCESS_ERROR: call_id={call_id}, error={str(e)}")
            raise

    async def list_tools(self, server: str) -> Dict[str, Any]:
        """List available tools from an MCP server for debugging"""
        start_time = asyncio.get_event_loop().time()
        call_id = str(uuid.uuid4())[:8]
        
        logger.info(f"🔍 MCP_LIST_TOOLS_START: call_id={call_id}, server={server}")
        
        try:
            if server not in self.servers:
                raise ValueError(f"Server '{server}' not configured")
            
            server_config = self.servers[server]
            
            # Create MCP request to list tools
            mcp_request = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "tools/list",
                "params": {}
            }
            
            result = await self._execute_mcp_call_simple(server_config, mcp_request, call_id)
            
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"✅ MCP_LIST_TOOLS_SUCCESS: call_id={call_id}, duration={duration:.3f}s")
            
            return result
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ MCP_LIST_TOOLS_FAILURE: call_id={call_id}, duration={duration:.3f}s, error={str(e)}")
            raise

    async def _execute_mcp_call_simple(self, server_config: Dict, mcp_request: Dict, call_id: str) -> Dict[str, Any]:
        """Simple MCP call execution for internal methods with enhanced stderr handling"""
        command = server_config.get('command')
        args = server_config.get('args', [])
        env = server_config.get('env', {})
        
        full_command = [command] + args
        
        # Prepare environment variables
        process_env = {**os.environ}
        if env:
            process_env.update(env)
        
        # Convert request to bytes
        request_json = json.dumps(mcp_request)
        request_data = (request_json + "\n").encode()
        
        logger.debug(f"🔧 MCP_SIMPLE_CALL: {request_json}")
        
        # Execute
        result = await asyncio.to_thread(
            subprocess.run,
            full_command,
            input=request_data,
            capture_output=True,
            env=process_env,
            timeout=30
        )
        
        stdout_content = result.stdout.decode() if result.stdout else ""
        stderr_content = result.stderr.decode() if result.stderr else ""
        
        # Enhanced stderr handling - treat MCP server initialization as success
        if stderr_content:
            if "Twitter MCP server running on stdio" in stderr_content:
                logger.info(f"✅ MCP_SERVER_READY: Twitter MCP server initialized successfully")
                logger.debug(f"🐦 MCP_SERVER_STATUS: {stderr_content}")
            else:
                logger.info(f"⚠️ MCP_STDERR_CONTENT: {stderr_content}")  # Show other stderr as warning
        
        if result.returncode != 0:
            raise Exception(f"MCP server returned code {result.returncode}: {stderr_content}")
        
        if not stdout_content:
            raise Exception("No stdout received from MCP server")
            
        response = json.loads(stdout_content)
        
        if 'error' in response:
            raise Exception(f"MCP server error: {response['error']}")
        
        return response.get('result', {}) 