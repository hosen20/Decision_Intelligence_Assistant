from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    # GROQ Configuration
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_model: str = Field("llama-3.3-70b-versatile", env="GROQ_MODEL")

    # Embedding Model
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")

    # Weaviate Configuration
    weaviate_url: str = Field("http://weaviate:8080", env="WEAVIATE_URL")
    weaviate_http_port: int = Field(8080, env="WEAVIATE_HTTP_PORT")
    weaviate_grpc_port: int = Field(50051, env="WEAVIATE_GRPC_PORT")
    weaviate_class_name: str = Field("SupportTicket", env="WEAVIATE_CLASS_NAME")

    # ML Configuration
    ml_model_path: str = Field("/app/models/ml_model.pkl", env="ML_MODEL_PATH")
    test_size: float = Field(0.2, env="TEST_SIZE")
    random_state: int = Field(42, env="RANDOM_STATE")

    # RAG Configuration
    top_k: int = Field(5, env="TOP_K")
    similarity_threshold: float = Field(0.7, env="SIMILARITY_THRESHOLD")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("/app/logs/app.log", env="LOG_FILE")

    # CORS
    cors_origins: List[str] = Field(
        ["http://frontend:3000", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )

    # FastAPI
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
