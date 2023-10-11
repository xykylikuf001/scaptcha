from typing import Optional
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Dirs
    BASE_DIR: Optional[str] = Path(__file__).resolve().parent.parent.parent.as_posix()
    PROJECT_DIR: Optional[str] = Path(__file__).resolve().parent.parent.as_posix()

    PAGE_URL: Optional[str] = "https://online.warrington.gov.uk/planning/index.html?fa=getApplication&id=211349"

    HEADLESS: Optional[bool] = False
    PROXY_ENABLED: Optional[bool] = False
    PROXY_AUTH_REQUIRED: Optional[bool] = False
    PROXY_FILENAME: Optional[str] = "files/proxy.txt"
    PROXY_CATEGORY: Optional[str] = 'r'
    PROXY_API: Optional[str] = None
    PROXY_TYPE: Optional[str] = "http"

    TWO_CAPTCHA_API_KEY: str

    MIN_THREADS: Optional[int] = 1
    MAX_THREADS: Optional[int] = 1

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env", env_file_encoding='utf-8',
        extra="ignore"
    )


settings = Settings()
