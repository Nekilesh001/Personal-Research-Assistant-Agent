"""
Structured markdown report generator.

Takes retrieved paper data, vector store chunks, and LLM to produce
a well-formatted research report following the standard template.
"""

from typing import List, Dict, Any
from datetime import datetime

from utils.logger import get_logger
from src.mode_handler import get_report_format_instructions

logger = get_logger(__name__)


async def generate_report(
    query: str,
    papers: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    llm: object,
    mode: str = "expert",
) -> str:
    """
    Generate a structured markdown research report using the LLM.

    Combines paper metadata and relevant chunks into a synthesis prompt,
    then uses the LLM to produce a formatted report.

    Args:
        query: The original research query.
        papers: List of paper metadata dictionaries.
        chunks: Relevant text chunks retrieved from the vector store.
        llm: A LangChain LLM instance.
        mode: 'expert' or 'beginner' — affects formatting and language.

    Returns:
        A complete markdown research report string.
    """
    logger.info(
        "report_generation_start",
        query=query[:80],
        num_papers=len(papers),
        num_chunks=len(chunks),
        mode=mode,
    )

    # Build context from papers
    papers_context = _build_papers_context(papers)

    # Build context from retrieved chunks
    chunks_context = _build_chunks_context(chunks)

    # Get format instructions for the selected mode
    format_instructions = get_report_format_instructions(mode)

    # Build the report generation prompt
    current_date = datetime.now().strftime("%B %d, %Y")
    paper_count = len(papers)

    prompt = f"""Based on the following academic papers and relevant excerpts, 
generate a comprehensive research report.

**Research Query:** {query}
**Date:** {current_date}
**Papers Analyzed:** {paper_count}
**Mode:** {mode}

---

## Papers Found:
{papers_context}

---

## Relevant Excerpts from Papers:
{chunks_context}

---

## Report Format Instructions:
{format_instructions}

Replace {{query}} with "{query}", {{date}} with "{current_date}", {{count}} with "{paper_count}", 
and {{mode}} with "{mode.capitalize()}" in the template.

IMPORTANT:
- Synthesize information across papers, don't just summarize each paper individually
- Always include the actual paper URLs as clickable links
- Identify patterns, agreements, and disagreements across papers
- Note methodological similarities and differences
- Assess the overall confidence based on the number and quality of sources
- If fewer than 3 papers were found, set confidence to "Low" and note this limitation

Generate the complete report now:"""

    try:
        response = await llm.ainvoke(prompt)
        report = response.content if hasattr(response, "content") else str(response)

        # Clean up any artifacts in the response
        report = _clean_report(report)

        logger.info("report_generation_success", length=len(report))
        return report

    except Exception as exc:
        logger.error("report_generation_failed", error=str(exc))
        return _generate_fallback_report(query, papers, current_date, mode)


def _build_papers_context(papers: List[Dict[str, Any]]) -> str:
    """
    Build a formatted context string from paper metadata.

    Args:
        papers: List of paper metadata dictionaries.

    Returns:
        Formatted string describing all papers.
    """
    if not papers:
        return "No papers were found for this query."

    lines = []
    for idx, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        authors = ", ".join(paper.get("authors", ["Unknown"]))
        year = paper.get("year", "N/A")
        url = paper.get("url", "")
        abstract = paper.get("abstract", "No abstract available.")
        source = paper.get("source", "unknown")
        citations = paper.get("citation_count")

        citation_info = f" | Citations: {citations}" if citations is not None else ""

        lines.append(
            f"### Paper {idx}: {title}\n"
            f"**Authors:** {authors}\n"
            f"**Year:** {year} | **Source:** {source}{citation_info}\n"
            f"**URL:** {url}\n"
            f"**Abstract:** {abstract}\n"
        )

    return "\n".join(lines)


def _build_chunks_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Build a formatted context string from retrieved vector store chunks.

    Args:
        chunks: List of chunk dictionaries with 'text' and 'metadata'.

    Returns:
        Formatted string with chunk excerpts and source attribution.
    """
    if not chunks:
        return "No additional context chunks are available."

    lines = []
    for idx, chunk in enumerate(chunks, 1):
        text = chunk.get("text", "")
        metadata = chunk.get("metadata", {})
        source_title = metadata.get("title", "Unknown source")
        score = chunk.get("rerank_score") or chunk.get("distance", "N/A")

        lines.append(
            f"**Excerpt {idx}** (from: {source_title}):\n"
            f"{text}\n"
        )

    return "\n".join(lines)


def _clean_report(report: str) -> str:
    """
    Clean up the generated report by removing common LLM artifacts.

    Args:
        report: Raw report text from the LLM.

    Returns:
        Cleaned report text.
    """
    # Remove leading/trailing whitespace
    report = report.strip()

    # Remove common LLM preamble phrases
    preamble_phrases = [
        "Here is the research report:",
        "Here's the research report:",
        "Here is your research report:",
        "Based on the analysis, here is the report:",
        "Sure, here is the report:",
        "```markdown",
        "```",
    ]

    for phrase in preamble_phrases:
        if report.startswith(phrase):
            report = report[len(phrase):].strip()
        if report.endswith(phrase):
            report = report[:-len(phrase)].strip()

    return report


def _generate_fallback_report(
    query: str,
    papers: List[Dict[str, Any]],
    date: str,
    mode: str,
) -> str:
    """
    Generate a basic fallback report when the LLM fails.

    Args:
        query: The research query.
        papers: Available paper metadata.
        date: Current date string.
        mode: Report mode.

    Returns:
        A basic markdown report string.
    """
    logger.warning("generating_fallback_report")

    paper_entries = []
    for paper in papers:
        title = paper.get("title", "Untitled")
        authors = ", ".join(paper.get("authors", ["Unknown"]))
        year = paper.get("year", "N/A")
        url = paper.get("url", "#")
        abstract = paper.get("abstract", "No abstract available.")

        paper_entries.append(
            f"- **{title}** — {authors} ({year}) [Read Paper →]({url})\n"
            f"  > {abstract[:200]}..."
        )

    papers_section = "\n\n".join(paper_entries) if paper_entries else "No papers found."

    return f"""# Research Report: {query}
**Generated:** {date} | **Papers analyzed:** {len(papers)} | **Mode:** {mode.capitalize()}

---

## Overview
This report was generated using a fallback mechanism due to an LLM processing error. 
Below are the papers that were found for your query. A complete synthesis could not be 
generated at this time.

## Key Papers
{papers_section}

## Key Findings
- The LLM was unable to synthesize findings at this time.
- Please review the paper abstracts above for relevant information.
- Try running the query again or switching LLM providers.

## Research Gaps & Open Questions
- Unable to analyze research gaps due to processing error.

## Suggested Reading
- Review the papers listed above for further exploration.

---
*Report confidence: Low — generated via fallback due to LLM error*
"""
