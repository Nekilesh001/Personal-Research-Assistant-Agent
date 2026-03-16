"""
SQLite database operations for query history, sessions, and saved reports.

Uses aiosqlite for async database access. The database file is
stored at SQLITE_DB_PATH (default: ./data/research_agent.db).
"""

import os
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

import aiosqlite
from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/research_agent.db")


async def init_db() -> None:
    """
    Initialize the SQLite database and create tables if they don't exist.

    Creates the following tables:
      - queries: stores query history with filters, mode, and timestamps
      - reports: stores generated reports linked to queries
    """
    # Ensure the directory exists
    db_dir = os.path.dirname(SQLITE_DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    logger.info("db_init_start", path=SQLITE_DB_PATH)

    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                query_id    TEXT PRIMARY KEY,
                query       TEXT NOT NULL,
                mode        TEXT NOT NULL DEFAULT 'expert',
                filters     TEXT DEFAULT '{}',
                paper_count INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id       TEXT PRIMARY KEY,
                query_id        TEXT NOT NULL,
                report_markdown TEXT NOT NULL,
                contradictions  TEXT DEFAULT '[]',
                followups       TEXT DEFAULT '[]',
                papers          TEXT DEFAULT '[]',
                created_at      TEXT NOT NULL,
                FOREIGN KEY (query_id) REFERENCES queries(query_id)
                    ON DELETE CASCADE
            )
        """)
        await db.commit()

    logger.info("db_init_success", path=SQLITE_DB_PATH)


async def save_query(
    query: str,
    mode: str,
    filters: Dict[str, Any],
) -> str:
    """
    Save a new query to the database.

    Args:
        query: The research query text.
        mode: 'expert' or 'beginner'.
        filters: FilterConfig as a dictionary.

    Returns:
        The generated query_id (UUID).
    """
    query_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO queries (query_id, query, mode, filters, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (query_id, query, mode, json.dumps(filters), now, now),
        )
        await db.commit()

    logger.info("query_saved", query_id=query_id, query=query[:80])
    return query_id


async def save_report(
    query_id: str,
    report_markdown: str,
    contradictions: List[Dict[str, Any]],
    followups: List[str],
    papers: List[Dict[str, Any]],
) -> str:
    """
    Save a generated report linked to a query.

    Args:
        query_id: The parent query's ID.
        report_markdown: Full markdown report text.
        contradictions: List of detected contradictions.
        followups: List of follow-up question strings.
        papers: List of paper metadata dicts.

    Returns:
        The generated report_id (UUID).
    """
    report_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO reports (report_id, query_id, report_markdown, contradictions, followups, papers, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                query_id,
                report_markdown,
                json.dumps(contradictions),
                json.dumps(followups),
                json.dumps(papers),
                now,
            ),
        )
        # Update paper count on the query record
        paper_count = len(papers)
        await db.execute(
            "UPDATE queries SET paper_count = ?, updated_at = ? WHERE query_id = ?",
            (paper_count, now, query_id),
        )
        await db.commit()

    logger.info("report_saved", report_id=report_id, query_id=query_id)
    return report_id


async def get_query_history(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve recent query history ordered by creation date (newest first).

    Args:
        limit: Maximum number of entries to return.

    Returns:
        List of query history dictionaries.
    """
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT
                q.query_id,
                q.query,
                q.mode,
                q.paper_count,
                q.created_at,
                CASE WHEN r.report_id IS NOT NULL THEN 1 ELSE 0 END as has_report
            FROM queries q
            LEFT JOIN reports r ON q.query_id = r.query_id
            ORDER BY q.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()

    return [
        {
            "query_id": row["query_id"],
            "query": row["query"],
            "mode": row["mode"],
            "paper_count": row["paper_count"],
            "created_at": row["created_at"],
            "has_report": bool(row["has_report"]),
        }
        for row in rows
    ]


async def get_report_by_id(query_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a saved report by its parent query ID.

    Args:
        query_id: The query ID whose report to fetch.

    Returns:
        Report dictionary if found, None otherwise.
    """
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT r.*, q.query, q.mode
            FROM reports r
            JOIN queries q ON r.query_id = q.query_id
            WHERE r.query_id = ?
            ORDER BY r.created_at DESC
            LIMIT 1
            """,
            (query_id,),
        )
        row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "report_id": row["report_id"],
        "query_id": row["query_id"],
        "query": row["query"],
        "mode": row["mode"],
        "report": row["report_markdown"],
        "contradictions": json.loads(row["contradictions"]),
        "followups": json.loads(row["followups"]),
        "papers": json.loads(row["papers"]),
        "created_at": row["created_at"],
    }


async def delete_query(query_id: str) -> bool:
    """
    Delete a query and its associated report from the database.

    Args:
        query_id: The ID of the query to delete.

    Returns:
        True if a row was deleted, False if the query_id was not found.
    """
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        # Delete report first (cascade may not be enforced)
        await db.execute(
            "DELETE FROM reports WHERE query_id = ?",
            (query_id,),
        )
        cursor = await db.execute(
            "DELETE FROM queries WHERE query_id = ?",
            (query_id,),
        )
        await db.commit()
        deleted = cursor.rowcount > 0

    if deleted:
        logger.info("query_deleted", query_id=query_id)
    else:
        logger.warning("query_not_found", query_id=query_id)

    return deleted
