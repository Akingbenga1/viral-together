import os
import json
from dotenv import load_dotenv
# from pydantic import BaseSettings
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET")
    OLLAMA_HOST: str = "http://localhost:11434"
    DOC_STORAGE_PATH: str = "app/static/docs/"
    
    # AI Agent Configuration
    AI_AGENTS_ENABLED: bool = os.getenv("AI_AGENTS_ENABLED", "true").lower() == "true"
    AI_AGENT_TOOL_CALLING_ENABLED: bool = os.getenv("AI_AGENT_TOOL_CALLING_ENABLED", "true").lower() == "true"
    AI_AGENT_MCP_ENABLED: bool = os.getenv("AI_AGENT_MCP_ENABLED", "true").lower() == "true"
    AI_AGENT_MAX_TOKENS: int = int(os.getenv("AI_AGENT_MAX_TOKENS", "2000"))
    AI_AGENT_TEMPERATURE: float = float(os.getenv("AI_AGENT_TEMPERATURE", "0.7"))
    AI_AGENT_TOP_P: float = float(os.getenv("AI_AGENT_TOP_P", "0.9"))
    
    # AI Agent Orchestration Configuration
    AI_AGENT_ORCHESTRATION_MODE: str = os.getenv("AI_AGENT_ORCHESTRATION_MODE", "llm")  # "llm", "database", "hybrid"
    AI_AGENT_LLM_ORCHESTRATION_ENABLED: bool = os.getenv("AI_AGENT_LLM_ORCHESTRATION_ENABLED", "true").lower() == "true"
    AI_AGENT_DATABASE_ORCHESTRATION_ENABLED: bool = os.getenv("AI_AGENT_DATABASE_ORCHESTRATION_ENABLED", "true").lower() == "true"
    AI_AGENT_TASK_COMPLEXITY_THRESHOLD: str = os.getenv("AI_AGENT_TASK_COMPLEXITY_THRESHOLD", "medium")  # "simple", "medium", "complex"
    AI_AGENT_ORCHESTRATION_MODEL: str = os.getenv("AI_AGENT_ORCHESTRATION_MODEL", "gemma3:1b")
    
    # MCP Server Configuration
    MCP_CONFIG_PATH: str = os.getenv("MCP_CONFIG_PATH", "mcp_config.json")
    MCP_SERVERS_ENABLED: bool = os.getenv("MCP_SERVERS_ENABLED", "true").lower() == "true"
    
    # Tool Calling Configuration
    WEB_SEARCH_ENABLED: bool = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    WEB_SEARCH_API_KEY: str = os.getenv("WEB_SEARCH_API_KEY", "")
    WEB_SEARCH_ENGINE: str = os.getenv("WEB_SEARCH_ENGINE", "google")  # google, bing, duckduckgo
    
    # Notification System Settings
    NOTIFICATIONS_ENABLED: bool = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"
    
    # Email Settings
    EMAIL_NOTIFICATIONS_ENABLED: bool = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    EMAIL_BACKEND: str = os.getenv("EMAIL_BACKEND", "smtp")  # 'smtp', 'sendgrid', 'mailgun'
    DEFAULT_EMAIL_FROM: str = os.getenv("DEFAULT_EMAIL_FROM", "noreply@viral-together.com")
    
    # SMTP Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "sandbox.smtp.mailtrap.io")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "2525"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # SendGrid Settings
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    
    # Mailgun Settings  
    MAILGUN_API_KEY: str = os.getenv("MAILGUN_API_KEY", "")
    MAILGUN_DOMAIN: str = os.getenv("MAILGUN_DOMAIN", "")
    
    # Twitter Settings
    TWITTER_NOTIFICATIONS_ENABLED: bool = os.getenv("TWITTER_NOTIFICATIONS_ENABLED", "true").lower() == "true"
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_TOKEN_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    
    # Ollama Settings for Tweet Generation
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # WebSocket Settings
    WEBSOCKET_ENABLED: bool = os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true"

    def get_mcp_config(self) -> Dict[str, Any]:
        """Load MCP configuration from JSON file"""
        try:
            if os.path.exists(self.MCP_CONFIG_PATH):
                with open(self.MCP_CONFIG_PATH, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Warning: Could not load MCP config: {e}")
            return {}

    class Config:
        env_file : str = ".env"

settings = Settings()
