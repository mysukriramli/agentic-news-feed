"""News feed and ingestion connectors."""

from .gdelt import GdeltConnector
from .wire_rss import WireRssConnector

__all__ = ["GdeltConnector", "WireRssConnector"]
