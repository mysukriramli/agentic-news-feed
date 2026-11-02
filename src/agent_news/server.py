from typing import List
from mcp.server.fastmcp import FastMCP
from .tools import get_breaking_news, search_news_by_keywords

mcp = FastMCP("agentic-news-feed")


@mcp.tool()
async def breaking_news(topic: str = "", max_age_hours: int = 24, limit: int = 20) -> str:
    """Fetch latest un-paywalled news filtered by topic or recency."""
    import json
    records = await get_breaking_news(topic=topic, max_age_hours=max_age_hours, limit=limit)
    return json.dumps(records, indent=2)


@mcp.tool()
async def search_news(keywords: List[str], since_hours: int = 48, limit: int = 20) -> str:
    """Full-text keyword search across ingested wire reports."""
    import json
    records = await search_news_by_keywords(keywords=keywords, since_hours=since_hours, limit=limit)
    return json.dumps(records, indent=2)


if __name__ == "__main__":
    mcp.run()
