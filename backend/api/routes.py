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

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from models.schemas import QueryRequest, ReportResponse
from models.llm_setup import test_llm_connection
from src.agent import run_research_pipeline
from utils.db import (
    save_query,
    save_report,
    get_query_history,
    get_report_by_id,
    get_query_by_id,
    delete_query,
)
from utils.logger import get_logger
from utils.pdf_generator import generate_pdf_bytes
from utils.pdf_extractor import extract_text_from_pdf, extract_metadata
from src.chat_handler import stream_chat_response, clear_chat_history, get_chat_history_list

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


@router.post("/search-papers")
async def search_papers(request: QueryRequest):
    """
    Search for papers WITHOUT generating a report.
    No LLM used — zero tokens spent.
    Returns list of paper objects for user to review.
    """
    import asyncio
    from src.tools import (
        fetch_arxiv_papers,
        fetch_semantic_scholar_papers,
    )

    query = request.query
    filters = request.filters
    paper_count = getattr(filters, 'paper_count', 10)
    # Convert enum to plain string for comparison
    source = str(getattr(filters, 'source', 'both'))
    if hasattr(filters.source, 'value'):
        source = filters.source.value

    sort_by_str = filters.sort_by.value if hasattr(filters.sort_by, 'value') else str(filters.sort_by)

    all_papers = []
    seen_titles = set()

    logger.info("search_papers_start", query=query[:60], source=source, paper_count=paper_count)

    # Fetch from arXiv (sync function — call .func to bypass @tool wrapper)
    if source in ('arxiv', 'both'):
        try:
            arxiv_raw = await asyncio.to_thread(
                fetch_arxiv_papers.func,
                query,
                paper_count,
                filters.year_from,
                filters.year_to,
                sort_by_str,
            )
            logger.info("arxiv_raw_result",
                        count=len(arxiv_raw) if isinstance(arxiv_raw, list) else 0,
                        sample=str(arxiv_raw[:1]) if isinstance(arxiv_raw, list) and arxiv_raw else "empty")
            if isinstance(arxiv_raw, list):
                for p in arxiv_raw:
                    if isinstance(p, dict) and 'error' not in p:
                        title = p.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            all_papers.append(p)
        except Exception as exc:
            logger.warning("search_arxiv_failed", error=str(exc))

    # Fetch from Semantic Scholar (sync function — call .func)
    if source in ('semantic_scholar', 'both'):
        try:
            ss_raw = await asyncio.to_thread(
                fetch_semantic_scholar_papers.func,
                query,
                paper_count,
                filters.year_from,
                filters.year_to,
                sort_by_str,
            )
            logger.info("ss_raw_result",
                        count=len(ss_raw) if isinstance(ss_raw, list) else 0,
                        sample=str(ss_raw[:1]) if isinstance(ss_raw, list) and ss_raw else "empty")
            if isinstance(ss_raw, list):
                for p in ss_raw:
                    if isinstance(p, dict) and 'error' not in p:
                        title = p.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            all_papers.append(p)
        except Exception as exc:
            logger.warning("search_ss_failed", error=str(exc))

    # Sort by citations if requested
    if sort_by_str == 'most_cited':
        all_papers.sort(
            key=lambda x: x.get('citation_count') or 0,
            reverse=True,
        )

    logger.info(
        "search_papers_complete",
        query=query[:60],
        total=len(all_papers[:paper_count])
    )
    return all_papers[:paper_count]


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

        # Push papers metadata to UI before finishing
        await event_queue.put({
            "type": "papers",
            "content": result.get("papers", []),
        })

    except Exception as exc:
        logger.error("pipeline_error", error=str(exc))
        await event_queue.put({
            "type": "error",
            "content": f"Research pipeline failed: {str(exc)}",
        })
    
    # Always send done event
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


@router.get("/history/{query_id}")
async def get_history_item(query_id: str) -> Dict[str, Any]:
    """
    Retrieve a single history item (query + report) by its ID.

    Args:
        query_id: The UUID of the query to fetch.

    Returns:
        The query and associated report data.
    """
    try:
        item = await get_query_by_id(query_id)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail=f"Query not found: {query_id}",
            )
        return item
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("history_item_fetch_failed", error=str(exc), query_id=query_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history item: {str(exc)}",
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


@router.get("/test-llm")
async def test_llm() -> Dict[str, Any]:
    """
    Test the LLM connection by sending a minimal prompt.

    Returns status, provider, model, latency, or exact error if it fails.
    Use this to verify API keys and connectivity before running queries.
    """
    result = await test_llm_connection()
    return result

# ---------------------------------------------------------
# PDF Export Endpoint
# ---------------------------------------------------------
@router.get("/report/{query_id}/pdf")
async def download_report_pdf(query_id: str) -> Response:
    """Download a saved report as a formatted PDF."""
    try:
        report = await get_report_by_id(query_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        report_text = (
            report.get("report")
            or report.get("markdown")
            or report.get("report_markdown")
            or ""
        )
        if not report_text:
            raise HTTPException(
                status_code=404,
                detail="Report content is empty"
            )
        pdf_bytes = generate_pdf_bytes(report_text)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="report_{query_id[:8]}.pdf"'
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("pdf_export_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

# ---------------------------------------------------------
# Paper Upload & Query Endpoints
# ---------------------------------------------------------
@router.post("/upload-papers")
async def upload_papers(files: list[UploadFile] = File(...)) -> list[Dict[str, Any]]:
    """Upload PDF papers, extract text/metadata, and store in vector db."""
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
        
    results = []
    papers_to_store = []
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append({"filename": file.filename, "status": "error", "message": "Only PDF files are supported"})
            continue
            
        try:
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:  # 10MB limit
                results.append({"filename": file.filename, "status": "error", "message": "File exceeds 10MB limit"})
                continue
                
            text = extract_text_from_pdf(content)
            if text.startswith("ERROR:"):
                results.append({"filename": file.filename, "status": "error", "message": text})
                continue
                
            metadata = extract_metadata(content)
            
            paper_data = {
                "title": metadata.get("title") or file.filename,
                "authors": metadata.get("authors", ["Unknown"]),
                "year": metadata.get("year", "N/A"),
                "url": f"uploaded://{file.filename}",
                "abstract": text,  # Override abstract with full text for chunking
                "source": "uploaded",
                "citation_count": 0
            }
            
            papers_to_store.append(paper_data)
            
            results.append({
                "filename": file.filename,
                "title": paper_data["title"],
                "page_count": metadata.get("page_count", 0),
                "status": "success"
            })
            
        except Exception as exc:
            logger.error("file_upload_error", filename=file.filename, error=str(exc))
            results.append({"filename": file.filename, "status": "error", "message": str(exc)})
            
    # Store successfully extracted papers into ChromaDB
    if papers_to_store:
        try:
            from utils.vector_store import store_papers
            store_papers(papers_to_store)
        except Exception as exc:
            logger.error("uploaded_papers_store_error", error=str(exc))
            
    return results

@router.post("/query-uploaded")
async def run_query_uploaded(request: QueryRequest) -> StreamingResponse:
    """Run research pipeline strictly using the uploaded papers in ChromaDB."""
    # Force the agent to only use uploaded source
    request.filters.source = "uploaded"
    logger.info("query_uploaded_received", query=request.query[:80])
    
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
        event_queue = asyncio.Queue(maxsize=100)
        pipeline_task = asyncio.create_task(
            _run_pipeline_safe(request, event_queue, query_id)
        )
        try:
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=120.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                event_data = json.dumps(event, default=str)
                yield f"data: {event_data}\n\n"
                if event.get("type") in ("done", "error"):
                    break
        except asyncio.CancelledError:
            pipeline_task.cancel()
        except Exception as exc:
            yield f'data: {{"type": "error", "content": "{str(exc)}"}}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# ---------------------------------------------------------
# Chat Endpoints
# ---------------------------------------------------------
class ChatMessage(BaseModel):
    message: str

@router.post("/chat/{query_id}")
async def chat_with_report(query_id: str, payload: ChatMessage) -> StreamingResponse:
    """Chat with the AI about a specific report."""
    report_data = await get_report_by_id(query_id)
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
        
    papers = report_data.get("papers", [])
    report_text = report_data.get("markdown", "")
    
    async def chat_stream():
        try:
            async for chunk in stream_chat_response(query_id, payload.message, report_text, papers):
                event_data = json.dumps({"chunk": chunk})
                yield f"data: {event_data}\n\n"
        except Exception as exc:
            event_data = json.dumps({"error": str(exc)})
            yield f"data: {event_data}\n\n"
            
    return StreamingResponse(
        chat_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.get("/chat/{query_id}/history")
async def get_chat_history(query_id: str) -> list:
    """Get the chat history for a report."""
    return get_chat_history_list(query_id)

@router.delete("/chat/{query_id}/history")
async def delete_chat_history(query_id: str):
    """Clear chat history for a report."""
    clear_chat_history(query_id)
    return {"status": "cleared"}
