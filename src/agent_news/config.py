from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_path: Path = Path("data/news.db")
    poll_interval_seconds: int = 900
    http_timeout_seconds: float = 15.0
    max_retries: int = 3
    backoff_factor: float = 1.5
    gdelt_enabled: bool = True
    rss_enabled: bool = True
    default_gdelt_query: str = "sourcelang:eng"
    rss_feed_urls: list[str] = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.reuters.com/reuters/topNews",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
