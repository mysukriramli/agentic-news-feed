# agentic-news-feed

Autonomous real-time, paywall-free global news ingestion and retrieval engine. Built for LLM multi-agent systems via Model Context Protocol (MCP) and Python function-calling interfaces.

## Capabilities
- **Paywall-Free Ingestion**: Streams wire reports via GDELT 2.0 Doc API and verified RSSHub endpoints.
- **SQLite FTS5 Storage**: Millisecond-level full-text keyword indexing and recency-ordered retrieval.
- **Deduplication Engine**: Deterministic SHA-256 fingerprinting on canonical URL and payload signatures.
- **Native MCP Interface**: FastMCP server exposing tools for Claude Desktop, Cursor, and ReAct frameworks.

## Quickstart

```bash
git clone [https://github.com/your-org/agentic-news-feed.git](https://github.com/your-org/agentic-news-feed.git)
cd agentic-news-feed
pip install -e .
