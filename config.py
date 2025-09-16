import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    openai_api_key: Optional[str] = None
    openai_assistant_id: Optional[str] = None
    
    chroma_persist_directory: str = "./chroma_db"
    
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    request_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    gail_base_url: str = "https://gailonline.com"
    gail_sitemap_url: str = "https://gailonline.com/sitemap.xml"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

Path(settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
