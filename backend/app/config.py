"""
Application configuration via pydantic-settings.
All values are loaded from environment variables or a .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "ProteinCraft"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://proteincraft:proteincraft@localhost:5432/proteincraft"

    # --- AI / ML ---
    esm_model_name: str = "facebook/esm2_t33_650M_UR50D"
    esm_device: str = "cpu"  # "cuda" if GPU available
    hf_api_token: str = ""

    # --- Gemini ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # --- ESMFold ---
    esmfold_api_url: str = "https://api.esmatlas.com/foldSequence/v1/pdb"
    esmfold_timeout: int = 120

    # --- Batch ---
    batch_max_size: int = 50
    batch_concurrency: int = 5

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — created once at startup."""
    return Settings()
