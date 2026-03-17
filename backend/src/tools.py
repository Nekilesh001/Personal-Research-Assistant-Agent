"""
LangChain tools for the research assistant agent.

Provides tools for:
  1. Fetching papers from arXiv
  2. Fetching papers from Semantic Scholar
  3. Searching the ChromaDB vector store
  4. Wikipedia overview search
  5. Query expansion via LLM
"""

import os
import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

import arxiv
import httpx
from bs4 import BeautifulSoup
from langchain.tools import tool
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

from utils.logger import get_logger
from utils.vector_store import search_similar, mmr_search, store_papers

load_dotenv()

logger = get_logger(__name__)

# CrossEncoder for re-ranking retrieved chunks
_cross_encoder: Optional[CrossEncoder] = None

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # seconds, exponential backoff base


def _get_cross_encoder() -> CrossEncoder:
    """
    Get or initialize the CrossEncoder model for re-ranking.

    Returns:
        A sentence-transformers CrossEncoder instance.
    """
    global _cross_encoder
    if _cross_encoder is None:
        model_name = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        _cross_encoder = CrossEncoder(model_name)
        logger.info("cross_encoder_init", model=model_name)
    return _cross_encoder


@tool
def fetch_arxiv_papers(
    query: str,
    max_results: int = 5,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort_by: str = "relevance",
) -> List[Dict[str, Any]]:
    """Fetch academic papers from arXiv.

    Args:
        query: Search query string.
        max_results: Maximum number of papers to return (1-20).
        year_from: Filter papers published on or after this year.
        year_to: Filter papers published on or before this year.
        sort_by: Sort order — 'relevance', 'most_recent', or 'most_cited'.

    Returns:
        List of paper dictionaries with title, authors, abstract, url, year, source.
    """
    logger.info("arxiv_fetch_start", query=query, max_results=max_results)

    # Map sort options to arxiv library's sort criteria
    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "most_recent": arxiv.SortCriterion.SubmittedDate,
        "most_cited": arxiv.SortCriterion.Relevance,  # arXiv doesn't support citation sort
    }
    sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)

    papers: List[Dict[str, Any]] = []

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results * 2,  # fetch extra for date filtering
            sort_by=sort_criterion,
            sort_order=arxiv.SortOrder.Descending,
        )

        for result in client.results(search):
            pub_year = result.published.year if result.published else None

            # Apply year filters
            if year_from and pub_year and pub_year < year_from:
                continue
            if year_to and pub_year and pub_year > year_to:
                continue

            paper = {
                "title": result.title.strip(),
                "authors": [str(a) for a in result.authors[:5]],
                "abstract": result.summary.strip(),
                "url": result.entry_id,
                "year": pub_year,
                "source": "arxiv",
                "citation_count": None,
                "doi": result.doi,
            }
            papers.append(paper)

            if len(papers) >= max_results:
                break

        logger.info("arxiv_fetch_success", papers_found=len(papers))

    except Exception as exc:
        logger.error("arxiv_fetch_failed", error=str(exc))
        return [{"error": f"arXiv fetch failed: {str(exc)}"}]

    return papers


@tool
def fetch_semantic_scholar_papers(
    query: str,
    max_results: int = 5,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort_by: str = "relevance",
) -> List[Dict[str, Any]]:
    """Fetch academic papers from Semantic Scholar API.

    Args:
        query: Search query string.
        max_results: Maximum number of papers to return (1-20).
        year_from: Filter papers published on or after this year.
        year_to: Filter papers published on or before this year.
        sort_by: Sort order — 'relevance', 'most_recent', or 'most_cited'.

    Returns:
        List of paper dictionaries with title, authors, abstract, url, year, source, citation_count.
    """
    logger.info("semantic_scholar_fetch_start", query=query, max_results=max_results)

    papers: List[Dict[str, Any]] = []

    # Build query parameters
    params: Dict[str, Any] = {
        "query": query,
        "limit": max_results,
        "fields": "title,authors,abstract,url,year,citationCount,externalIds",
    }

    # Year filter
    if year_from or year_to:
        year_range = f"{year_from or ''}-{year_to or ''}"
        params["year"] = year_range

    # Sort mapping
    if sort_by == "most_cited":
        params["sort"] = "citationCount:desc"
    elif sort_by == "most_recent":
        params["sort"] = "year:desc"

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(SEMANTIC_SCHOLAR_API, params=params)
                response.raise_for_status()
                data = response.json()

            for item in data.get("data", []):
                abstract = item.get("abstract") or ""
                if not abstract:
                    continue

                authors = [
                    a.get("name", "Unknown")
                    for a in (item.get("authors") or [])[:5]
                ]

                # Build paper URL
                paper_url = item.get("url", "")
                external_ids = item.get("externalIds") or {}
                if not paper_url and external_ids.get("DOI"):
                    paper_url = f"https://doi.org/{external_ids['DOI']}"
                elif not paper_url and external_ids.get("ArXiv"):
                    paper_url = f"https://arxiv.org/abs/{external_ids['ArXiv']}"

                paper = {
                    "title": (item.get("title") or "Untitled").strip(),
                    "authors": authors,
                    "abstract": abstract.strip(),
                    "url": paper_url,
                    "year": item.get("year"),
                    "source": "semantic_scholar",
                    "citation_count": item.get("citationCount"),
                    "doi": external_ids.get("DOI"),
                }
                papers.append(paper)

            logger.info("semantic_scholar_fetch_success", papers_found=len(papers))
            return papers

        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code == 429:
                # Rate limited — wait and retry
                wait_time = RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(
                    "semantic_scholar_rate_limited",
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                )
                import time
                time.sleep(wait_time)
                continue
            else:
                logger.error("semantic_scholar_http_error", status=exc.response.status_code)
                break

        except Exception as exc:
            last_error = exc
            logger.error("semantic_scholar_fetch_failed", error=str(exc), attempt=attempt + 1)
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_DELAY_BASE * (2 ** attempt))
                continue
            break

    logger.warning("semantic_scholar_all_retries_failed", error=str(last_error))
    return [{"error": f"Semantic Scholar fetch failed after {MAX_RETRIES} retries: {str(last_error)}"}]


@tool
def search_vector_store(
    query: str,
    n_results: int = 10,
    use_mmr: bool = True,
    rerank: bool = True,
) -> List[Dict[str, Any]]:
    """Search the vector store for relevant paper chunks.

    Uses MMR for diverse retrieval, then optionally re-ranks with CrossEncoder.

    Args:
        query: The search query.
        n_results: Number of results to return.
        use_mmr: Whether to use MMR for diversity (vs plain similarity).
        rerank: Whether to re-rank results with CrossEncoder.

    Returns:
        List of relevant text chunks with metadata and scores.
    """
    logger.info("vector_search_start", query=query[:60], n_results=n_results)

    try:
        if use_mmr:
            results = mmr_search(query, n_results=n_results * 2 if rerank else n_results)
        else:
            results = search_similar(query, n_results=n_results * 2 if rerank else n_results)

        if not results:
            logger.info("vector_search_no_results")
            return []

        # Re-rank with CrossEncoder if requested
        if rerank and len(results) > 1:
            results = _rerank_results(query, results, top_k=n_results)

        logger.info("vector_search_complete", results=len(results))
        return results[:n_results]

    except Exception as exc:
        logger.error("vector_search_failed", error=str(exc))
        return []


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for a field overview related to the research query.

    Provides background context and general knowledge about a topic.

    Args:
        query: The topic to search for on Wikipedia.

    Returns:
        A summary string from Wikipedia, or an error message.
    """
    logger.info("wikipedia_search_start", query=query[:60])

    try:
        import wikipedia
        wikipedia.set_lang("en")

        # Search for the most relevant page
        search_results = wikipedia.search(query, results=3)
        if not search_results:
            return f"No Wikipedia results found for: {query}"

        # Try to get a summary from the best match
        for result_title in search_results:
            try:
                summary = wikipedia.summary(result_title, sentences=5)
                logger.info("wikipedia_search_success", title=result_title)
                return f"**Wikipedia: {result_title}**\n\n{summary}"
            except wikipedia.DisambiguationError as de:
                # Try the first suggested option
                if de.options:
                    try:
                        summary = wikipedia.summary(de.options[0], sentences=5)
                        logger.info("wikipedia_search_disambiguation", title=de.options[0])
                        return f"**Wikipedia: {de.options[0]}**\n\n{summary}"
                    except Exception:
                        continue
            except wikipedia.PageError:
                continue

        return f"No detailed Wikipedia article found for: {query}"

    except Exception as exc:
        logger.error("wikipedia_search_failed", error=str(exc))
        return f"Wikipedia search failed: {str(exc)}"


async def expand_query(query: str, llm: object, filters: Optional[Any] = None) -> List[str]:
    """
    Use the LLM to expand a vague query into 2-3 specific search terms.
    Incorporates domain and keywords if provided.

    Args:
        query: The original user query.
        llm: A LangChain LLM instance.
        filters: Optional FilterConfig for better context.

    Returns:
        List of 2-3 expanded search terms.
    """
    context_str = ""
    if filters:
        if getattr(filters, 'domain', None):
            context_str += f"\n- Context Domain: {filters.domain}"
        if getattr(filters, 'keywords', None) and len(filters.keywords) > 0:
            context_str += f"\n- Must include topics: {', '.join(filters.keywords)}"

    logger.info("query_expansion_start", original_query=query[:80], context=context_str.strip())

    expansion_prompt = f"""You are a research query expansion expert. 
Given the following research query and additional context, generate exactly 3 specific, focused search terms 
that would help find the most relevant academic papers. 
{context_str}

Original query: "{query}"

Rules:
- Each search term should be specific and academic
- Cover different aspects or angles of the topic
- Use technical terminology that would appear in paper titles/abstracts
- If a 'Context Domain' or 'Keywords' are provided, ensure they are integrated into the search terms.
- Return ONLY the search terms, one per line, no numbering, no extra text

Search terms:"""

    try:
        response = await llm.ainvoke(expansion_prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse the response into individual search terms
        terms = [
            line.strip().strip("-•*1234567890.)")
            for line in content.strip().split("\n")
            if line.strip() and len(line.strip()) > 3
        ]

        # Ensure we have 1-3 terms
        expanded = terms[:3] if terms else [query]

        logger.info("query_expansion_success", terms=expanded)
        return expanded

    except Exception as exc:
        logger.warning("query_expansion_failed", error=str(exc))
        return [query]


def _rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Re-rank search results using a CrossEncoder for true relevance scoring.

    Args:
        query: The original search query.
        results: List of search results to re-rank.
        top_k: Number of top results to keep after re-ranking.

    Returns:
        Re-ranked list of results, sorted by CrossEncoder score (descending).
    """
    try:
        cross_encoder = _get_cross_encoder()

        # Build query-document pairs for the CrossEncoder
        pairs = [[query, result["text"]] for result in results]
        scores = cross_encoder.predict(pairs)

        # Attach scores and sort
        for result, score in zip(results, scores):
            result["rerank_score"] = float(score)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        logger.info("rerank_complete", original=len(results), top_k=top_k)
        return results[:top_k]

    except Exception as exc:
        logger.warning("rerank_failed", error=str(exc))
        return results[:top_k]


def get_all_tools() -> list:
    """
    Get all tools available to the research agent.

    Returns:
        List of LangChain tool instances.
    """
    return [
        fetch_arxiv_papers,
        fetch_semantic_scholar_papers,
        search_vector_store,
        wikipedia_search,
    ]
