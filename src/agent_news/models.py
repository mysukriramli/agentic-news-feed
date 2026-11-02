import hashlib
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class NewsArticle(BaseModel):
    id: str = Field(description="Deterministic SHA256 of canonical URL or title")
    title: str = Field(..., min_length=3)
    summary: str = Field(default="")
    canonical_url: str = Field(...)
    source_domain: str = Field(...)
    published_at: datetime = Field(...)
    language: str = Field(default="en")
    sentiment_score: Optional[float] = Field(default=None)
    keywords: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("id", mode="before")
    @classmethod
    def generate_id_if_empty(cls, v: Optional[str], info) -> str:
        if v:
            return v
        data = info.data
        unique_key = data.get("canonical_url") or data.get("title") or ""
        return hashlib.sha256(unique_key.encode("utf-8")).hexdigest()

    @field_validator("published_at", mode="before")
    @classmethod
    def parse_datetime(cls, v) -> datetime:
        if isinstance(v, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y%m%d%H%M%S",
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S GMT",
            ):
                try:
                    return datetime.strptime(v, fmt).astimezone(timezone.utc)
                except ValueError:
                    continue
            return datetime.fromisoformat(v).astimezone(timezone.utc)
        if isinstance(v, datetime):
            return v.astimezone(timezone.utc)
        return datetime.now(timezone.utc)


class IngestPayload(BaseModel):
    source_type: str
    articles: list[NewsArticle]
    total_received: int
    total_valid: int
    duration_ms: float


class AgentQueryRequest(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    topic: Optional[str] = Field(default=None)
    since_hours: int = Field(default=24, ge=1, le=168)
    limit: int = Field(default=20, ge=1, le=100)
    language: Optional[str] = Field(default="en")
