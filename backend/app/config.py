from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mediassist.db"
    app_secret: str = "development-only-change-me"
    upload_dir: str = "./data/uploads"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_origins: str = "http://localhost:5173"
    session_ttl_hours: int = 12
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    use_vector_retrieval: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
