from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""

    data_dir: Path = Path("data")
    ytdlp_cookies_file: Optional[Path] = None

    # Models
    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o"
    deepseek_model: str = "deepseek-chat"
    
    # Legacy support (can be removed later if unused)
    transcribe_model: str = "gemini-2.0-flash"
    factcheck_model: str = "gemini-2.0-flash"

    @field_validator("ytdlp_cookies_file", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v


settings = Settings()
