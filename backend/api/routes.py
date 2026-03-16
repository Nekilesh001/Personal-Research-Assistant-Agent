"""
FastAPI route definitions for the Personal Research Assistant Agent.

Defines all API endpoints including:
  - POST /api/query — runs agent pipeline with SSE streaming
  - GET  /api/history — returns query history from SQLite
  - GET  /api/report/{id} — returns a saved report by query ID
  - DELETE /api/history/{id} — deletes a query from history
  - GET  /api/health — health check
  - GET  /api/domains — available research domain list
"""

import asyncio
import json
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import QueryRequest, ReportResponse
from src.agent import run_research_pipeline
from utils.db import (
    save_query,
    save_report,
    get_query_history,
    get_report_by_id,
    delete_query,
)
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["research"])

# Available research domains
RESEARCH_DOMAINS = [
    "Computer Science",
    "Artificial Intelligence",
    "Machine Learning",
    "Natural Language Processing",
    "Computer Vision",
    "Robotics",
    "Biology",
    "Neuroscience",
    "Genetics",
    "Physics",
    "Quantum Computing",
    "Mathematics",
    "Medicine",
    "Pharmacology",
    "Chemistry",
    "Materials Science",
    "Economics",
    "Finance",
    "Psychology",
    "Environmental Science",
    "Climate Science",
    "Astronomy",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Education",
]


@router.post("/query")
async def run_query(request: QueryRequest) -> StreamingResponse:
    """
    Run a research query and stream results via Server-Sent Events.

    The agent pipeline runs asynchronously, streaming reasoning steps
    (thought, action, observation) in real-time, followed by the
    report, contradictions, and follow-up questions.

    Args:
        request: The incoming QueryRequest.

    Returns:
        A StreamingResponse with SSE-formatted events.
    """
    logger.info("query_received", query=request.query[:80], mode=request.mode)

    # Save the query to history
    try:
        query_id = await save_query(
            query=request.query,
            mode=request.mode,
            filters=request.filters.model_dump(),
        )
    except Exception as exc:
        logger.error("query_save_failed", error=str(exc))
        query_id = "error-no-db"

    async def event_stream():
        """Generate SSE events from the research pipeline."""
        event_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        # Run the pipeline in a background task
        pipeline_task = asyncio.create_task(
            _run_pipeline_safe(request, event_queue, query_id)
        )

        try:
            while True:
                try:
                    # Wait for events with a timeout
                    event = await asyncio.wait_for(
                        event_queue.get(),
                        timeout=120.0,
                    )
                except asyncio.TimeoutError:
                    # Send a keepalive comment
                    yield ": keepalive\n\n"
                    continue

                # Format as SSE
                event_data = json.dumps(event, default=str)
                yield f"data: {event_data}\n\n"

                # Break on "done" or "error" events
                if event.get("type") in ("done", "error"):
                    break

        except asyncio.CancelledError:
            pipeline_task.cancel()
            logger.warning("sse_stream_cancelled")
        except Exception as exc:
            error_event = json.dumps({"type": "error", "content": str(exc)})
            yield f"data: {error_event}\n\n"
            logger.error("sse_stream_error", error=str(exc))

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


async def _run_pipeline_safe(
    request: QueryRequest,
    event_queue: asyncio.Queue,
    query_id: str,
) -> None:
    """
    Run the research pipeline with error handling and report saving.

    Args:
        request: The query request.
        event_queue: Queue for SSE events.
        query_id: The database query ID.
    """
    try:
        result = await run_research_pipeline(
            request=request,
            event_queue=event_queue,
        )

        # Save the report to the database
        try:
            await save_report(
                query_id=query_id,
                report_markdown=result["report"],
                contradictions=result["contradictions"],
                followups=result["followups"],
                papers=result["papers"],
            )
        except Exception as exc:
            logger.error("report_save_failed", error=str(exc))

    except Exception as exc:
        logger.error("pipeline_error", error=str(exc))
        await event_queue.put({
            "type": "error",
            "content": f"Research pipeline failed: {str(exc)}",
        })
        await event_queue.put({"type": "done", "content": ""})


@router.get("/history")
async def get_history() -> list:
    """
    Retrieve the query history from the database.

    Returns:
        List of query history entries (newest first).
    """
    try:
        history = await get_query_history(limit=50)
        return history
    except Exception as exc:
        logger.error("history_fetch_failed", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch query history: {str(exc)}",
        )


@router.get("/report/{query_id}")
async def get_report(query_id: str) -> Dict[str, Any]:
    """
    Retrieve a saved report by its query ID.

    Args:
        query_id: The UUID of the query whose report to fetch.

    Returns:
        The report data including markdown, contradictions, followups, and papers.
    """
    try:
        report = await get_report_by_id(query_id)
        if report is None:
            raise HTTPException(
                status_code=404,
                detail=f"No report found for query ID: {query_id}",
            )
        return report
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("report_fetch_failed", error=str(exc), query_id=query_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch report: {str(exc)}",
        )


@router.delete("/history/{query_id}")
async def delete_history_entry(query_id: str) -> Dict[str, str]:
    """
    Delete a query and its report from the history.

    Args:
        query_id: The UUID of the query to delete.

    Returns:
        Confirmation message.
    """
    try:
        deleted = await delete_query(query_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Query not found: {query_id}",
            )
        return {"message": f"Query {query_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("history_delete_failed", error=str(exc), query_id=query_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete query: {str(exc)}",
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status and timestamp.
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Personal Research Assistant Agent",
    }


@router.get("/domains")
async def get_domains() -> list:
    """
    Get the list of available research domains.

    Returns:
        List of domain name strings.
    """
    return RESEARCH_DOMAINS
