from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "ContractSense"
    app_version: str = "0.0.1"
    debug: bool = True

    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    chroma_persist_dir: str = "./chroma_db"


    class Config:
        # Use absolute path to .env file
        env_file = str(Path(__file__).parent.parent / ".env")
        # ignore unknown keys from env so extra settings are tolerated
        extra = "ignore"

settings = Settings()