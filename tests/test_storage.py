import pytest
from datetime import datetime, timezone
from pathlib import Path
from agent_news.models import NewsArticle
from agent_news.storage import NewsStorage


@pytest.mark.asyncio
async def test_upsert_and_recency_search(tmp_path: Path):
    db_file = tmp_path / "test_news.db"
    storage = NewsStorage(db_file)
    await storage.initialize()

    article = NewsArticle(
        id="test_sha256_hash",
        title="Autonomous Systems Advance in Energy Grid Automation",
        summary="Engineers deploy multi-agent controls across municipal power distribution nodes.",
        canonical_url="https://example.com/energy-grid-automation",
        source_domain="example.com",
        published_at=datetime.now(timezone.utc),
        language="en",
        keywords=["energy", "automation", "ai"],
    )

    inserted = await storage.upsert_articles([article])
    assert inserted == 1

    results = await storage.search_recent(keywords=["energy"], since_hours=24)
    assert len(results) == 1
    assert results[0].id == "test_sha256_hash"
    assert results[0].title == article.title


@pytest.mark.asyncio
async def test_fts_exact_matching(tmp_path: Path):
    db_file = tmp_path / "test_fts.db"
    storage = NewsStorage(db_file)
    await storage.initialize()

    article1 = NewsArticle(
        id="1",
        title="Semiconductor Fabrication Plant Opens in Dresden",
        summary="High-volume European wafer production begins.",
        canonical_url="https://example.com/chips-dresden",
        source_domain="example.com",
        published_at=datetime.now(timezone.utc),
        language="en",
    )
    article2 = NewsArticle(
        id="2",
        title="Maritime Shipping Rates Ease Along Pacific Routes",
        summary="Container pricing returns to seasonal equilibrium.",
        canonical_url="https://example.com/shipping-rates",
        source_domain="example.com",
        published_at=datetime.now(timezone.utc),
        language="en",
    )

    await storage.upsert_articles([article1, article2])

    matches = await storage.search_recent(keywords=["Semiconductor"], since_hours=12)
    assert len(matches) == 1
    assert matches[0].id == "1"
