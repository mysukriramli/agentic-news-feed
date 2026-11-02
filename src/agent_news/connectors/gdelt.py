import asyncio
import hashlib
from typing import List
from urllib.parse import urlparse
import httpx

from ..models import NewsArticle


class GdeltConnector:
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, timeout_seconds: float = 15.0, max_retries: int = 3, backoff: float = 1.5):
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.backoff = backoff

    async def fetch_articles(self, query: str = "sourcelang:eng", max_records: int = 75) -> List[NewsArticle]:
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(max_records),
            "sort": "datedesc"
        }
        articles: List[NewsArticle] = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(self.BASE_URL, params=params)
                    if response.status_code == 429:
                        await asyncio.sleep(self.backoff * (attempt + 1))
                        continue
                    response.raise_for_status()
                    data = response.json()
                    raw_items = data.get("articles", [])
                    for item in raw_items:
                        url = item.get("url")
                        title = item.get("title")
                        if not url or not title:
                            continue
                        domain = item.get("domain") or urlparse(url).netloc
                        art_id = hashlib.sha256(url.encode("utf-8")).hexdigest()
                        tone = item.get("tone")
                        sentiment = float(tone) if tone is not None else None
                        
                        articles.append(NewsArticle(
                            id=art_id,
                            title=title,
                            summary=item.get("seendate", ""),
                            canonical_url=url,
                            source_domain=domain,
                            published_at=item.get("seendate", ""),
                            language=item.get("language", "en"),
                            sentiment_score=sentiment,
                            keywords=[item.get("sourcecountry", "")]
                        ))
                    return articles
                except (httpx.RequestError, httpx.HTTPStatusError):
                    if attempt == self.max_retries - 1:
                        return []
                    await asyncio.sleep(self.backoff * (attempt + 1))
        return articles
