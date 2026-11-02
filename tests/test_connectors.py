import pytest
from agent_news.connectors.gdelt import GdeltConnector
from agent_news.connectors.wire_rss import WireRssConnector


@pytest.mark.asyncio
async def test_gdelt_connector_contract():
    connector = GdeltConnector(timeout_seconds=5.0, max_retries=1)
    articles = await connector.fetch_articles(query="sourcelang:eng", max_records=2)
    assert isinstance(articles, list)
    for art in articles:
        assert art.id is not None
        assert art.title != ""
        assert art.canonical_url.startswith("http")


@pytest.mark.asyncio
async def test_wire_rss_connector_contract():
    connector = WireRssConnector(timeout_seconds=5.0, max_retries=1)
    articles = await connector.fetch_feed("https://feeds.bbci.co.uk/news/world/rss.xml")
    assert isinstance(articles, list)
    if articles:
        assert articles[0].id is not None
        assert articles[0].source_domain != ""
