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
    
    # Multi-Source Data Configuration
    # Data Source Toggles
    MCP_ENABLED: bool = os.getenv("MCP_ENABLED", "false").lower() == "true"
    DIRECT_API_ENABLED: bool = os.getenv("DIRECT_API_ENABLED", "false").lower() == "true"
    THIRD_PARTY_ENABLED: bool = os.getenv("THIRD_PARTY_ENABLED", "false").lower() == "true"
    
    # MCP Server Configuration
    MCP_TWITTER_ENABLED: bool = os.getenv("MCP_TWITTER_ENABLED", "false").lower() == "true"
    MCP_YOUTUBE_ENABLED: bool = os.getenv("MCP_YOUTUBE_ENABLED", "false").lower() == "true"
    MCP_TIKTOK_ENABLED: bool = os.getenv("MCP_TIKTOK_ENABLED", "false").lower() == "true"
    MCP_INSTAGRAM_ENABLED: bool = os.getenv("MCP_INSTAGRAM_ENABLED", "false").lower() == "true"
    MCP_FACEBOOK_ENABLED: bool = os.getenv("MCP_FACEBOOK_ENABLED", "false").lower() == "true"
    MCP_LINKEDIN_ENABLED: bool = os.getenv("MCP_LINKEDIN_ENABLED", "false").lower() == "true"
    
    # Direct API Configuration
    DIRECT_API_TWITTER_ENABLED: bool = os.getenv("DIRECT_API_TWITTER_ENABLED", "false").lower() == "true"
    DIRECT_API_YOUTUBE_ENABLED: bool = os.getenv("DIRECT_API_YOUTUBE_ENABLED", "false").lower() == "true"
    DIRECT_API_TIKTOK_ENABLED: bool = os.getenv("DIRECT_API_TIKTOK_ENABLED", "false").lower() == "true"
    DIRECT_API_INSTAGRAM_ENABLED: bool = os.getenv("DIRECT_API_INSTAGRAM_ENABLED", "false").lower() == "true"
    DIRECT_API_FACEBOOK_ENABLED: bool = os.getenv("DIRECT_API_FACEBOOK_ENABLED", "false").lower() == "true"
    DIRECT_API_LINKEDIN_ENABLED: bool = os.getenv("DIRECT_API_LINKEDIN_ENABLED", "false").lower() == "true"
    
    # 3rd Party Services Configuration
    THIRD_PARTY_SOCIALBLADE_ENABLED: bool = os.getenv("THIRD_PARTY_SOCIALBLADE_ENABLED", "false").lower() == "true"
    THIRD_PARTY_HOOTSUITE_ENABLED: bool = os.getenv("THIRD_PARTY_HOOTSUITE_ENABLED", "false").lower() == "true"
    THIRD_PARTY_SPROUT_ENABLED: bool = os.getenv("THIRD_PARTY_SPROUT_ENABLED", "false").lower() == "true"
    THIRD_PARTY_BRANDWATCH_ENABLED: bool = os.getenv("THIRD_PARTY_BRANDWATCH_ENABLED", "false").lower() == "true"
    THIRD_PARTY_BUFFER_ENABLED: bool = os.getenv("THIRD_PARTY_BUFFER_ENABLED", "false").lower() == "true"
    THIRD_PARTY_LATER_ENABLED: bool = os.getenv("THIRD_PARTY_LATER_ENABLED", "false").lower() == "true"
    
    # Tool Calling Configuration
    WEB_SEARCH_ENABLED: bool = os.getenv("WEB_SEARCH_ENABLED", "false").lower() == "true"
    WEB_SEARCH_API_KEY: str = os.getenv("WEB_SEARCH_API_KEY", "")
    WEB_SEARCH_ENGINE: str = os.getenv("WEB_SEARCH_ENGINE", "duckduckgo")  # google, bing, duckduckgo
    
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
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")
    
    # WebSocket Settings
    WEBSOCKET_ENABLED: bool = os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true"
    
    # Enhanced AI Agent Settings
    ENHANCED_AI_AGENTS_ENABLED: bool = os.getenv("ENHANCED_AI_AGENTS_ENABLED", "true").lower() == "true"
    REAL_TIME_DATA_CACHE_TTL: int = int(os.getenv("REAL_TIME_DATA_CACHE_TTL", "300"))  # 5 minutes
    MAX_CONCURRENT_AGENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_AGENT_REQUESTS", "10"))
    
    # Social Media API Settings
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_BUSINESS_ID: str = os.getenv("INSTAGRAM_BUSINESS_ID", "")
    FACEBOOK_APP_ID: str = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET: str = os.getenv("FACEBOOK_APP_SECRET", "")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    TIKTOK_ACCESS_TOKEN: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    TIKTOK_CLIENT_KEY: str = os.getenv("TIKTOK_CLIENT_KEY", "")
    TIKTOK_CLIENT_SECRET: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    
    # 3rd Party Analytics API Keys
    SOCIALBLADE_API_KEY: str = os.getenv("SOCIALBLADE_API_KEY", "")
    HOOTSUITE_API_KEY: str = os.getenv("HOOTSUITE_API_KEY", "")
    HOOTSUITE_CLIENT_ID: str = os.getenv("HOOTSUITE_CLIENT_ID", "")
    HOOTSUITE_CLIENT_SECRET: str = os.getenv("HOOTSUITE_CLIENT_SECRET", "")
    SPROUT_SOCIAL_API_KEY: str = os.getenv("SPROUT_SOCIAL_API_KEY", "")
    BRANDWATCH_API_KEY: str = os.getenv("BRANDWATCH_API_KEY", "")
    BUFFER_API_KEY: str = os.getenv("BUFFER_API_KEY", "")
    LATER_API_KEY: str = os.getenv("LATER_API_KEY", "")
    
    # Web Search Settings
    WEB_SEARCH_ENGINE_ID: str = os.getenv("WEB_SEARCH_ENGINE_ID", "")
    
    # Location Settings
    LOCATION_SERVICE_PROVIDER: str = os.getenv("LOCATION_SERVICE_PROVIDER", "openstreetmap")  # openstreetmap, google
    DEFAULT_SEARCH_RADIUS_KM: int = int(os.getenv("DEFAULT_SEARCH_RADIUS_KM", "50"))
    MAX_SEARCH_RADIUS_KM: int = int(os.getenv("MAX_SEARCH_RADIUS_KM", "500"))
    
    # OpenStreetMap Settings
    OSM_USER_AGENT: str = os.getenv("OSM_USER_AGENT", "ViralTogether/1.0")
    OSM_BASE_URL: str = os.getenv("OSM_BASE_URL", "https://nominatim.openstreetmap.org")
    
    # Google Maps Settings (for future use)
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    GOOGLE_MAPS_BASE_URL: str = os.getenv("GOOGLE_MAPS_BASE_URL", "https://maps.googleapis.com")

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
