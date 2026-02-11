from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):
    """Application configuration"""
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "value_investing_research"
    POSTGRES_USER: str = "researcher"
    POSTGRES_PASSWORD: str
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # LLM APIs
    OPENROUTER_API_KEY: Optional[str] = None
    
    # App Settings
    DAILY_INSIGHT_COUNT: int = 5
    INSIGHT_SCORE_THRESHOLD: float = 7.0
    
    @property
    def postgres_params(self):
        return {
            "host": self.POSTGRES_HOST,
            "port": self.POSTGRES_PORT,
            "dbname": self.POSTGRES_DB,
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD
        }
        
    @property
    def redis_params(self):
        return {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT
        }

    class Config:
        env_file = ".env"
        extra = "ignore"
