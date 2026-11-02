from typing import List, Dict, Any, Optional
from .config import get_settings
from .storage import NewsStorage


async def get_breaking_news(topic: str = "", max_age_hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieves real-time global news indexed by recency and filtered by topic or keywords.
    """
    settings = get_settings()
    storage = NewsStorage(settings.database_path)
    await storage.initialize()

    articles = await storage.search_recent(
        topic=topic if topic.strip() else None,
        since_hours=max_age_hours,
        limit=limit,
    )

    return [
        {
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "source": a.source_domain,
            "url": a.canonical_url,
            "published_at": a.published_at.isoformat(),
            "sentiment_score": a.sentiment_score,
        }
        for a in articles
    ]


async def search_news_by_keywords(keywords: List[str], since_hours: int = 48, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Performs full-text inverted-index search across ingested global articles using discrete keyword tokens.
    """
    settings = get_settings()
    storage = NewsStorage(settings.database_path)
    await storage.initialize()

    articles = await storage.search_recent(
        keywords=keywords,
        since_hours=since_hours,
        limit=limit,
    )

    return [
        {
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "source": a.source_domain,
            "url": a.canonical_url,
            "published_at": a.published_at.isoformat(),
            "sentiment_score": a.sentiment_score,
            "keywords": a.keywords,
        }
        for a in articles
    ]
