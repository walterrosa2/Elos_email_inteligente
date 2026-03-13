from pathlib import Path
from pydantic import Field
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Force reload .env to override system environment variables (that might be stale)
load_dotenv(override=True)

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Pipeline V2.1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Audit (V2.2)
    DEV_AUDIT_MODE: bool = True # Enable to save intermediate JSONs
    RETENCAO_DIAS: int = 30 # Log retention in days

    # Database
    DATABASE_URL: str = "sqlite:///./dados/app_v2.db"

    # OpenAI / LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"

    # AWS / Textract
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Email / IMAP
    IMAP_SERVER: Optional[str] = Field("outlook.office365.com", validation_alias="EMAIL_HOST")
    IMAP_PORT: int = Field(993, validation_alias="EMAIL_PORT")
    IMAP_USER: Optional[str] = Field(None, validation_alias="EMAIL_USER")
    IMAP_PASSWORD: Optional[str] = Field(None, validation_alias="EMAIL_PASSWORD")
    
    # OAuth2 (Microsoft)
    USE_OAUTH2: bool = True
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None

    # Paths
    STORAGE_PATH: str = "dados/storage"
    DATA_ROOT: Path = Path("dados")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
