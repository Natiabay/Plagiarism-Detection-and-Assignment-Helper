from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "academic_helper"
    POSTGRES_USER: str = "student"
    POSTGRES_PASSWORD: str = "secure_password_123"
    
    # OpenAI
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    
    # JWT
    JWT_SECRET_KEY: str = "academic-helper-jwt-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # FastAPI
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    
    # n8n
    N8N_WEBHOOK_URL: str = "https://nati1221.app.n8n.cloud/webhook/plagiarism-check"
    # Called after student reviews results and confirms sending to instructor
    N8N_TEACHER_WEBHOOK_URL: str = "https://nati1221.app.n8n.cloud/webhook/teacher-notify"
    
    # Notifications
    TEACHER_EMAIL: str = "instructor@example.com"
    
    # Application
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Vector
    VECTOR_DIMENSION: int = 1536
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

