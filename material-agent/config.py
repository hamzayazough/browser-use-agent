from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: str
    browser_use_api_key: Optional[str] = None
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = True
    reload: bool = True
    
    # MongoDB Configuration
    mongodb_uri: str
    
    # Client Configuration
    server_url: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"
    
    # Logging
    log_level: str = "info"
    
    # Vector Database Configuration
    vector_db_provider: str = "mongodb"  # 'mongodb' or 'pinecone'
    
    # Pinecone Configuration (optional, for production)
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index_name: Optional[str] = None
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ca-central-1"
    aws_s3_bucket: str = "chat-plot"
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Validation Thresholds
    minimum_total_score: int = 12
    minimum_license_score: int = 3
    minimum_chunks_per_objective: int = 2
    minimum_sources_per_topic: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
