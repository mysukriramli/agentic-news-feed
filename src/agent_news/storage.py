from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
import aiosqlite
import json

from .models import NewsArticle


class NewsStorage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    canonical_url TEXT NOT NULL UNIQUE,
                    source_domain TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    language TEXT NOT NULL,
                    sentiment_score REAL,
                    keywords_json TEXT NOT NULL,
                    ingested_at TEXT NOT NULL
                );
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_published_at 
                ON articles(published_at DESC);
            """)
            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                    id UNINDEXED,
                    title,
                    summary,
                    source_domain,
                    tokenize='porter unicode61'
                );
            """)
            await db.commit()

    async def upsert_articles(self, articles: List[NewsArticle]) -> int:
        if not articles:
            return 0
        inserted_count = 0
        async with aiosqlite.connect(self.db_path) as db:
            for art in articles:
                cursor = await db.execute("""
                    INSERT INTO articles (
                        id, title, summary, canonical_url, source_domain, 
                        published_at, language, sentiment_score, keywords_json, ingested_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        summary=excluded.summary,
                        sentiment_score=excluded.sentiment_score
                    RETURNING id;
                """, (
                    art.id,
                    art.title,
                    art.summary,
                    art.canonical_url,
                    art.source_domain,
                    art.published_at.isoformat(),
                    art.language,
                    art.sentiment_score,
                    json.dumps(art.keywords),
                    art.ingested_at.isoformat(),
                ))
                row = await cursor.fetchone()
                if row:
                    inserted_count += 1
                    await db.execute("""
                        DELETE FROM articles_fts WHERE id = ?;
                    """, (art.id,))
                    await db.execute("""
                        INSERT INTO articles_fts (id, title, summary, source_domain)
                        VALUES (?, ?, ?, ?);
                    """, (art.id, art.title, art.summary, art.source_domain))
            await db.commit()
        return inserted_count

    async def search_recent(
        self,
        keywords: Optional[List[str]] = None,
        topic: Optional[str] = None,
        since_hours: int = 24,
        limit: int = 50,
        language: Optional[str] = "en"
    ) -> List[NewsArticle]:
        cutoff_dt = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
        query_parts = []
        params = [cutoff_dt]

        fts_query_tokens = []
        if keywords:
            fts_query_tokens.extend([f'"{k}"' for k in keywords])
        if topic:
            fts_query_tokens.append(f'"{topic}"')

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if fts_query_tokens:
                fts_expr = " AND ".join(fts_query_tokens)
                sql = """
                    SELECT a.* FROM articles a
                    JOIN articles_fts f ON a.id = f.id
                    WHERE articles_fts MATCH ?
                      AND a.published_at >= ?
                """
                params = [fts_expr, cutoff_dt]
                if language:
                    sql += " AND a.language = ?"
                    params.append(language)
                sql += " ORDER BY a.published_at DESC LIMIT ?;"
                params.append(limit)
            else:
                sql = """
                    SELECT * FROM articles
                    WHERE published_at >= ?
                """
                if language:
                    sql += " AND language = ?"
                    params.append(language)
                sql += " ORDER BY published_at DESC LIMIT ?;"
                params.append(limit)

            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                results.append(NewsArticle(
                    id=r["id"],
                    title=r["title"],
                    summary=r["summary"],
                    canonical_url=r["canonical_url"],
                    source_domain=r["source_domain"],
                    published_at=r["published_at"],
                    language=r["language"],
                    sentiment_score=r["sentiment_score"],
                    keywords=json.loads(r["keywords_json"]),
                    ingested_at=r["ingested_at"],
                ))
            return results
