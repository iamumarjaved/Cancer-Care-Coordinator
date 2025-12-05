"""Configuration settings for Cancer Care Coordinator."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    APP_NAME: str = "Cancer Care Coordinator"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # API Settings
    API_PREFIX: str = "/api/v1"

    # CORS Settings - parse from environment or use defaults
    @property
    def CORS_ORIGINS(self) -> list:
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            return [origin.strip() for origin in cors_env.split(",")]
        return ["http://localhost:3000", "http://127.0.0.1:3000", "https://healthcare.umarjaved.me"]

    # OpenAI Settings (for LLM calls)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")  # gpt-4o-mini for 128k context

    # Mock Mode Settings (for prototype/testing)
    # Defaults to False for production - uses real OpenAI API
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
    USE_MOCK_VECTOR_STORE: bool = os.getenv("USE_MOCK_VECTOR_STORE", "false").lower() == "true"
    USE_MOCK_TRIALS_API: bool = os.getenv("USE_MOCK_TRIALS_API", "false").lower() == "true"

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cancer_care.db")

    # ChromaDB Settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # Feature Flags
    ENABLE_RAG: bool = True
    ENABLE_STREAMING: bool = True

    # Agent Settings
    MAX_AGENT_RETRIES: int = 3
    AGENT_TIMEOUT_SECONDS: int = 30

    # Vector Store Settings
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "cancer-care-coordinator")

    # Embedding Settings
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536

    # RAG Settings
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # Clerk Authentication Settings
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_JWKS_URL: str = os.getenv("CLERK_JWKS_URL", "")
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"

    # LangSmith Tracing Settings (free tier: https://smith.langchain.com)
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "cancer-care-coordinator")
    LANGSMITH_TRACING_ENABLED: bool = os.getenv("LANGSMITH_TRACING_ENABLED", "false").lower() == "true"

    # SendGrid Email Settings
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "")
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "true").lower() == "true"


settings = Settings()
