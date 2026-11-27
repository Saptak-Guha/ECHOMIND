"""
EchoMind Configuration
All application settings loaded from environment variables.
"""

from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional

# A bare ".env" resolves against the process working directory, so running
# uvicorn from backend/ silently loaded nothing — the real file sits at the repo
# root. Resolve both absolutely so the settings load from any cwd.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent
# Later files win, so a backend-local .env can still override the shared one.
_ENV_FILES = (str(_REPO_ROOT / ".env"), str(_BACKEND_DIR / ".env"))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "EchoMind"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PostgreSQL
    POSTGRES_USER: str = "echomind"
    POSTGRES_PASSWORD: str = "echomind_secret"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "echomind"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "echomind_neo4j"

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./data/chromadb"

    # FAISS
    FAISS_INDEX_DIR: str = "./data/faiss"

    # JWT Auth
    JWT_SECRET_KEY: str = "echomind-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Embedding
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_BATCH_SIZE: int = 100

    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # LLM provider selection: "auto" walks anthropic → openai → ollama and
    # falls through whenever one is unusable. Set a name to pin one.
    LLM_PROVIDER: str = "auto"

    # Ollama — local models, no API key, no cost
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT_SECONDS: float = 180.0

    # Anthropic (preferred provider when set)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-opus-5"

    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def _ignore_placeholder_anthropic_key(cls, v: Optional[str]) -> Optional[str]:
        """Same placeholder handling as the OpenAI key."""
        if v is None:
            return None
        v = v.strip()
        if not v or not v.startswith("sk-ant-") or "your-" in v or "key-here" in v:
            return None
        return v

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def _ignore_placeholder_key(cls, v: Optional[str]) -> Optional[str]:
        """Treat the .env.example placeholder as "no key".

        Every AI engine gates on `if settings.OPENAI_API_KEY:` and falls back to
        local heuristics when it is None. A placeholder string is truthy, so it
        would build a client with a bogus key and 401 on every call instead of
        taking the fallback path.
        """
        if v is None:
            return None
        v = v.strip()
        if not v or not v.startswith("sk-") or "your-o" in v or "key-here" in v:
            return None
        return v

    class Config:
        env_file = _ENV_FILES
        case_sensitive = True


settings = Settings()
