import asyncio
import logging
import time
from typing import List

from .config import get_settings
from .connectors.gdelt import GdeltConnector
from .connectors.wire_rss import WireRssConnector
from .models import NewsArticle
from .storage import NewsStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("news_pipeline")


class NewsPipeline:
    def __init__(self):
        self.settings = get_settings()
        self.storage = NewsStorage(self.settings.database_path)
        self.gdelt = GdeltConnector(
            timeout_seconds=self.settings.http_timeout_seconds,
            max_retries=self.settings.max_retries,
            backoff=self.settings.backoff_factor,
        )
        self.rss = WireRssConnector(
            timeout_seconds=self.settings.http_timeout_seconds,
            max_retries=self.settings.max_retries,
            backoff=self.settings.backoff_factor,
        )

    async def run_once(self) -> int:
        start_time = time.perf_counter()
        collected: List[NewsArticle] = []

        if self.settings.gdelt_enabled:
            logger.info("Executing GDELT ingestion cycle...")
            gdelt_articles = await self.gdelt.fetch_articles(query=self.settings.default_gdelt_query)
            collected.extend(gdelt_articles)
            logger.info("GDELT produced %d records", len(gdelt_articles))

        if self.settings.rss_enabled:
            logger.info("Executing RSS ingestion cycle across %d feeds...", len(self.settings.rss_feed_urls))
            rss_tasks = [self.rss.fetch_feed(url) for url in self.settings.rss_feed_urls]
            results = await asyncio.gather(*rss_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    collected.extend(res)

        dedup_map = {a.id: a for a in collected}
        unique_articles = list(dedup_map.values())
        persisted = await self.storage.upsert_articles(unique_articles)
        duration = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Cycle completed in %.2fms. Ingested: %d, Unique: %d, Committed: %d",
            duration,
            len(collected),
            len(unique_articles),
            persisted,
        )
        return persisted

    async def start(self) -> None:
        await self.storage.initialize()
        logger.info("News pipeline initialized with target DB: %s", self.settings.database_path)
        while True:
            try:
                await self.run_once()
            except Exception as e:
                logger.error("Error encountered in ingestion pipeline: %s", str(e), exc_info=True)
            await asyncio.sleep(self.settings.poll_interval_seconds)


if __name__ == "__main__":
    pipeline = NewsPipeline()
    asyncio.run(pipeline.start())
