import asyncio
import hashlib
from typing import List
from urllib.parse import urlparse
import feedparser
import httpx

from ..models import NewsArticle


class WireRssConnector:
    def __init__(self, timeout_seconds: float = 15.0, max_retries: int = 3, backoff: float = 1.5):
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.backoff = backoff

    async def fetch_feed(self, feed_url: str) -> List[NewsArticle]:
        articles: List[NewsArticle] = []
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            content = None
            for attempt in range(self.max_retries):
                try:
                    res = await client.get(feed_url, headers={"User-Agent": "AgenticNewsFeed/1.0"})
                    if res.status_code == 429:
                        await asyncio.sleep(self.backoff * (attempt + 1))
                        continue
                    res.raise_for_status()
                    content = res.text
                    break
                except (httpx.RequestError, httpx.HTTPStatusError):
                    if attempt == self.max_retries - 1:
                        return []
                    await asyncio.sleep(self.backoff * (attempt + 1))

        if not content:
            return []

        parsed = await asyncio.to_thread(feedparser.parse, content)
        for entry in parsed.entries:
            link = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            if not link or not title:
                continue
            
            domain = urlparse(link).netloc
            art_id = hashlib.sha256(link.encode("utf-8")).hexdigest()
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            pub_date = getattr(entry, "published", None) or getattr(entry, "updated", None)

            tags = [t.term for t in getattr(entry, "tags", []) if hasattr(t, "term")]

            articles.append(NewsArticle(
                id=art_id,
                title=title,
                summary=summary,
                canonical_url=link,
                source_domain=domain,
                published_at=pub_date or "",
                language="en",
                sentiment_score=None,
                keywords=tags
            ))

        return articles
