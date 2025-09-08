"""
Configuration settings for the GAIL RAG Chatbot System.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_assistant_id: Optional[str] = None
    
    # Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    
    # Web Scraping Configuration
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    request_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    
    # Application Configuration
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # GAIL Website Configuration
    gail_base_url: str = "https://gailonline.com"
    gail_sitemap_url: str = "https://gailonline.com/sitemap.xml"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
