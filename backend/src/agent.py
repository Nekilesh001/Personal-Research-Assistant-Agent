"""
LangChain ReAct agent core for the Personal Research Assistant.

Orchestrates the research pipeline:
  1. Query expansion (vague → specific search terms)
  2. Paper fetching from arXiv and Semantic Scholar
  3. Embedding and storing in ChromaDB
  4. Retrieval and re-ranking
  5. Report generation
  6. Contradiction detection
  7. Follow-up question generation

Streams reasoning steps (Thought → Action → Observation) via callbacks.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

from models.llm_setup import get_llm
from models.schemas import FilterConfig, QueryRequest
from src.tools import (
    get_all_tools,
    expand_query,
    fetch_arxiv_papers,
    fetch_semantic_scholar_papers,
    search_vector_store,
)
from src.mode_handler import get_system_prompt, apply_mode_defaults
from src.report_generator import generate_report
from src.contradiction_detector import detect_contradictions
from src.followup_generator import generate_followups
from utils.vector_store import store_papers
from utils.logger import get_logger

logger = get_logger(__name__)

# Shared conversation memory across sessions
_session_memories: Dict[str, ConversationBufferMemory] = {}


# ReAct agent prompt template
REACT_PROMPT_TEMPLATE = """{{system_prompt}}

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must research
Thought: think about what to do step by step
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to compile the report
Final Answer: the final synthesized research report

Important instructions:
- Always expand vague queries into specific search terms first
- Search BOTH arXiv and Semantic Scholar for comprehensive coverage
- After fetching papers, search the vector store for relevant stored chunks
- Cite paper URLs in your final report so readers can access sources
- Note when papers contradict each other
- Identify research gaps and open questions

Begin!

Question: {input}
{agent_scratchpad}

Chat History:
{chat_history}"""


class StreamingCallbackHandler(BaseCallbackHandler):
    """
    Callback handler that captures agent reasoning steps for SSE streaming.

    Collects Thought, Action, and Observation events into a queue
    that the SSE endpoint reads from.
    """

    def __init__(self) -> None:
        """Initialize the streaming callback handler."""
        super().__init__()
        self.events: List[Dict[str, str]] = []
        self._queue: Optional[asyncio.Queue] = None

    def set_queue(self, queue: asyncio.Queue) -> None:
        """
        Set the asyncio queue for sending events.

        Args:
            queue: The asyncio Queue to push events to.
        """
        self._queue = queue

    def _push_event(self, event_type: str, content: str) -> None:
        """
        Push an event to the queue and internal list.

        Args:
            event_type: The event type (thought, action, observation).
            content: The event content text.
        """
        event = {"type": event_type, "content": content}
        self.events.append(event)
        if self._queue:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("event_queue_full")

    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Handle agent action events."""
        self._push_event("action", f"Using tool: {action.tool}")
        self._push_event("thought", action.log.strip() if action.log else "")

    def on_agent_finish(self, finish: Any, **kwargs: Any) -> None:
        """Handle agent finish events."""
        self._push_event("thought", "Compiling final report...")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Handle tool start events."""
        tool_name = serialized.get("name", "unknown")
        self._push_event("action", f"Calling {tool_name}...")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Handle tool end events."""
        # Truncate long tool outputs for the stream
        truncated = output[:300] + "..." if len(str(output)) > 300 else str(output)
        self._push_event("observation", truncated)

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Handle LLM start events."""
        pass  # Skip to avoid noise in the stream

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Handle LLM end events."""
        pass  # Output is captured by agent action/finish handlers

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Handle chain error events."""
        self._push_event("error", f"Error: {str(error)}")


def get_memory(session_id: str = "default") -> ConversationBufferMemory:
    """
    Get or create a ConversationBufferMemory for the given session.

    Args:
        session_id: Session identifier for memory isolation.

    Returns:
        A ConversationBufferMemory instance.
    """
    if session_id not in _session_memories:
        _session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )
        logger.info("memory_created", session_id=session_id)

    return _session_memories[session_id]


def _create_agent(
    llm: object,
    system_prompt: str,
) -> AgentExecutor:
    """
    Create a ReAct agent with all tools and memory.

    Args:
        llm: The LLM instance.
        system_prompt: Mode-specific system prompt.

    Returns:
        An AgentExecutor ready to run.
    """
    tools = get_all_tools()

    # Build the prompt template with the system prompt injected
    template = REACT_PROMPT_TEMPLATE.replace("{{system_prompt}}", system_prompt)

    prompt = PromptTemplate(
        template=template,
        input_variables=["input", "agent_scratchpad", "chat_history"],
        partial_variables={
            "tools": "\n".join([f"- {t.name}: {t.description}" for t in tools]),
            "tool_names": ", ".join([t.name for t in tools]),
        },
    )

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=8,
        early_stopping_method="force",
        return_intermediate_steps=True,
    )


async def run_research_pipeline(
    request: QueryRequest,
    event_queue: asyncio.Queue,
    session_id: str = "default",
) -> Dict[str, Any]:
    """
    Execute the full research pipeline for a query.

    This is the main orchestration function that:
      1. Expands the query
      2. Fetches papers from configured sources
      3. Stores them in the vector store
      4. Runs the ReAct agent for synthesis
      5. Generates the report, contradictions, and follow-ups

    Args:
        request: The incoming QueryRequest.
        event_queue: asyncio Queue for streaming events to the client.
        session_id: Session ID for conversation memory.

    Returns:
        Dictionary with report, contradictions, followups, and papers.
    """
    logger.info(
        "pipeline_start",
        query=request.query[:80],
        mode=request.mode,
    )

    # Initialize LLM
    llm = get_llm(streaming=True)

    # Apply mode-specific filter defaults
    filters = apply_mode_defaults(request.filters, request.mode)

    # Step 1: Query expansion
    await _send_event(event_queue, "thought", "Analyzing your query and generating specific search terms...")
    expanded_queries = expand_query(request.query, llm)
    await _send_event(
        event_queue,
        "observation",
        f"Expanded query into: {', '.join(expanded_queries)}",
    )

    # Step 2: Fetch papers
    all_papers: List[Dict[str, Any]] = []

    if filters.source in ("arxiv", "both"):
        await _send_event(event_queue, "action", "Searching arXiv for papers...")
        for eq in expanded_queries:
            try:
                arxiv_papers = fetch_arxiv_papers.invoke({
                    "query": eq,
                    "max_results": filters.paper_count,
                    "year_from": filters.year_from,
                    "year_to": filters.year_to,
                    "sort_by": filters.sort_by.value,
                })
                if arxiv_papers and not any("error" in p for p in arxiv_papers):
                    all_papers.extend(arxiv_papers)
                    await _send_event(
                        event_queue,
                        "observation",
                        f"Found {len(arxiv_papers)} papers on arXiv for '{eq}'",
                    )
            except Exception as exc:
                logger.warning("arxiv_pipeline_error", error=str(exc))
                await _send_event(event_queue, "thought", f"arXiv search encountered an issue: {str(exc)[:100]}")

    if filters.source in ("semantic_scholar", "both"):
        await _send_event(event_queue, "action", "Searching Semantic Scholar for papers...")
        for eq in expanded_queries:
            try:
                ss_papers = fetch_semantic_scholar_papers.invoke({
                    "query": eq,
                    "max_results": filters.paper_count,
                    "year_from": filters.year_from,
                    "year_to": filters.year_to,
                    "sort_by": filters.sort_by.value,
                })
                if ss_papers and not any("error" in p for p in ss_papers):
                    all_papers.extend(ss_papers)
                    await _send_event(
                        event_queue,
                        "observation",
                        f"Found {len(ss_papers)} papers on Semantic Scholar for '{eq}'",
                    )
            except Exception as exc:
                logger.warning("semantic_scholar_pipeline_error", error=str(exc))
                await _send_event(event_queue, "thought", f"Semantic Scholar search encountered an issue: {str(exc)[:100]}")

    # Deduplicate papers by title
    all_papers = _deduplicate_papers(all_papers)

    # Limit to requested count
    all_papers = all_papers[:filters.paper_count]

    if not all_papers:
        await _send_event(
            event_queue,
            "thought",
            "No papers found. Try broader keywords or a different date range.",
        )
        return {
            "report": "# No Papers Found\n\nNo academic papers matched your query. Try:\n- Using broader search terms\n- Expanding the date range\n- Checking spelling\n- Trying a different research source",
            "contradictions": [],
            "followups": [
                f"What are the fundamentals of {request.query}?",
                f"Latest reviews on {request.query}",
                f"Key researchers in {request.query}",
            ],
            "papers": [],
        }

    await _send_event(
        event_queue,
        "observation",
        f"Total unique papers found: {len(all_papers)}",
    )

    # Step 3: Store papers in vector store
    await _send_event(event_queue, "action", "Embedding papers into vector store...")
    try:
        chunks_stored = store_papers(all_papers)
        await _send_event(
            event_queue,
            "observation",
            f"Stored {chunks_stored} text chunks in the vector store",
        )
    except Exception as exc:
        logger.error("vector_store_pipeline_error", error=str(exc))
        await _send_event(event_queue, "thought", "Vector store encountered an issue, continuing with paper data...")

    # Step 4: Retrieve relevant chunks
    await _send_event(event_queue, "action", "Retrieving most relevant paper excerpts...")
    try:
        chunks = search_vector_store.invoke({
            "query": request.query,
            "n_results": 10,
            "use_mmr": True,
            "rerank": True,
        })
    except Exception as exc:
        logger.warning("retrieval_error", error=str(exc))
        chunks = []

    await _send_event(
        event_queue,
        "observation",
        f"Retrieved {len(chunks)} relevant excerpts from vector store",
    )

    # Step 5: Generate the report
    await _send_event(event_queue, "thought", "Synthesizing findings into a structured report...")
    report = await generate_report(
        query=request.query,
        papers=all_papers,
        chunks=chunks if isinstance(chunks, list) else [],
        llm=llm,
        mode=request.mode,
    )
    await _send_event(event_queue, "report", report)

    # Step 6: Detect contradictions
    await _send_event(event_queue, "action", "Checking for contradictions between papers...")
    contradictions = await detect_contradictions(
        papers=all_papers,
        chunks=chunks if isinstance(chunks, list) else [],
        llm=llm,
    )
    await _send_event(event_queue, "contradictions", contradictions)

    # Step 7: Generate follow-up questions
    await _send_event(event_queue, "action", "Generating follow-up research questions...")
    followups = await generate_followups(
        query=request.query,
        report=report,
        papers=all_papers,
        llm=llm,
        mode=request.mode,
    )
    await _send_event(event_queue, "followups", followups)

    # Update conversation memory
    memory = get_memory(session_id)
    memory.save_context(
        {"input": request.query},
        {"output": report[:500]},  # Save first 500 chars to avoid memory bloat
    )

    # Step 8: Done
    await _send_event(event_queue, "done", "")

    papers_serialized = [
        {
            "title": p.get("title", ""),
            "authors": p.get("authors", []),
            "abstract": p.get("abstract", "")[:300],
            "url": p.get("url", ""),
            "year": p.get("year"),
            "source": p.get("source", ""),
            "citation_count": p.get("citation_count"),
        }
        for p in all_papers
    ]

    logger.info(
        "pipeline_complete",
        papers=len(all_papers),
        contradictions=len(contradictions),
        followups=len(followups),
    )

    return {
        "report": report,
        "contradictions": contradictions,
        "followups": followups,
        "papers": papers_serialized,
    }


def _deduplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate papers based on title similarity.

    Args:
        papers: List of paper dictionaries.

    Returns:
        Deduplicated list of papers.
    """
    seen_titles = set()
    unique_papers = []

    for paper in papers:
        # Normalize title for comparison
        title = paper.get("title", "").lower().strip()
        title_key = "".join(c for c in title if c.isalnum())

        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_papers.append(paper)

    logger.info(
        "papers_deduplicated",
        original=len(papers),
        unique=len(unique_papers),
    )
    return unique_papers


async def _send_event(
    queue: asyncio.Queue,
    event_type: str,
    content: Any,
) -> None:
    """
    Send an event to the SSE queue.

    Args:
        queue: The asyncio Queue.
        event_type: Event type string.
        content: Event content.
    """
    try:
        await queue.put({"type": event_type, "content": content})
    except Exception as exc:
        logger.warning("event_send_failed", type=event_type, error=str(exc))
