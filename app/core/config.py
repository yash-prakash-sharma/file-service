from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "File Service"
    DATABASE_URL: str
    LOGIN_SERVICE_URL: str
    
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION_NAME: str = "us-east-1"
    AWS_BUCKET_NAME: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
