import asyncio
from pathlib import Path
from agent_news.pipeline import NewsPipeline
from agent_news.tools import get_breaking_news, search_news_by_keywords

async def main():
    print("=" * 60)
    print("AGENTIC-NEWS-FEED: INGESTION CYCLE & FTS RETRIEVAL")
    print("=" * 60)

    pipeline = NewsPipeline()
    await pipeline.storage.initialize()

    # 1. Fetch live articles from GDELT 2.0 & Wire RSS Feeds
    print("\n[1/3] Ingesting latest unpaywalled wire feeds...")
    inserted = await pipeline.run_once()
    print(f"Successfully committed {inserted} fresh articles to SQLite FTS5.")

    # 2. Check Database File
    db_file = Path("data/news.db")
    if db_file.exists():
        print(f"\n[2/3] Database verified at {db_file} ({db_file.stat().st_size} bytes).")

    # 3. Simulate Autonomous Agent Retrieving Breaking News
    print("\n[3/3] Querying breaking news via Agent Tool...")
    top_news = await get_breaking_news(max_age_hours=24, limit=5)
    for idx, item in enumerate(top_news, 1):
        print(f"\n{idx}. [{item['source']}] {item['title']}")
        print(f"   Published: {item['published_at']}")
        print(f"   URL: {item['url']}")

if __name__ == "__main__":
    asyncio.run(main())
