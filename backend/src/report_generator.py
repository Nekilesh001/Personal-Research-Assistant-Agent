"""
Structured markdown report generator with depth enforcement.

Takes retrieved paper data, vector store chunks, and LLM to produce
a well-formatted research report. Includes:
  - Token counting to prevent context overflow
  - Retry logic via invoke_with_retry
  - Content validation with expansion passes
  - Real error messages in fallback reports
"""

from typing import List, Dict, Any
from datetime import datetime

from utils.logger import get_logger
from utils.chunker import get_token_count
from src.mode_handler import get_report_format_instructions
from models.llm_setup import invoke_with_retry

logger = get_logger(__name__)

# Token budget for the LLM prompt
MAX_PROMPT_TOKENS = 28000
# Minimum content thresholds
MIN_OVERVIEW_WORDS = 200
MIN_KEY_FINDINGS = 6
MIN_RESEARCH_GAPS = 4


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
    then uses the LLM to produce a formatted report. Includes token budget
    management and content depth validation.

    Args:
        query: The original research query.
        papers: List of paper metadata dictionaries.
        chunks: Relevant text chunks retrieved from the vector store.
        llm: A LangChain LLM instance.
        mode: 'expert' or 'beginner' -- affects formatting and language.

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

    prompt = f"""Based on the following academic papers and relevant excerpts, \
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

Replace {{{{query}}}} with "{query}", {{{{date}}}} with "{current_date}", \
{{{{count}}}} with "{paper_count}", and {{{{mode}}}} with "{mode.capitalize()}" \
in the template.

CRITICAL INSTRUCTIONS:
- Synthesize information ACROSS papers, do not just summarize each individually
- The Overview section MUST be at least 3 full paragraphs (200+ words)
- Key Findings MUST have at least 6 specific bullet points with evidence
- Research Gaps MUST have at least 4 specific open questions
- Always include actual paper URLs as clickable links
- Cite paper titles and authors when making claims
- Identify patterns, agreements, and disagreements across papers
- Note methodological similarities and differences
- Assess overall confidence based on the number and quality of sources
- If fewer than 3 papers were found, set confidence to "Low" and note this

Generate the complete report now:"""

    # Check token count and truncate if necessary
    token_count = get_token_count(prompt)
    logger.info("report_prompt_tokens", tokens=token_count, max=MAX_PROMPT_TOKENS)

    if token_count > MAX_PROMPT_TOKENS:
        logger.warning(
            "prompt_too_long_truncating",
            tokens=token_count,
            max=MAX_PROMPT_TOKENS,
        )
        prompt = _truncate_prompt(
            query, papers, chunks, format_instructions,
            current_date, paper_count, mode,
        )
        token_count = get_token_count(prompt)
        logger.info("truncated_prompt_tokens", tokens=token_count)

    try:
        # Use retry logic for resilient LLM calls
        report = await invoke_with_retry(llm, prompt, max_retries=3, base_delay=2.0)

        # Clean up LLM artifacts
        report = _clean_report(report)

        # Validate content depth and expand if needed
        report = await _validate_and_expand(report, query, papers, llm, mode)

        logger.info("report_generation_success", length=len(report))
        return report

    except Exception as exc:
        error_msg = str(exc)
        error_type = type(exc).__name__
        logger.error(
            "report_generation_failed",
            error_type=error_type,
            error=error_msg,
        )
        print(f"\n[REPORT ERROR] {error_type}: {error_msg}\n")
        # FIXED: was error_msg=error_msg, now correctly error_message=error_msg
        return _generate_fallback_report(
            query, papers, current_date, mode, error_message=error_msg
        )


def _truncate_prompt(
    query: str,
    papers: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    format_instructions: str,
    current_date: str,
    paper_count: int,
    mode: str,
) -> str:
    """
    Build a truncated prompt that fits within the token budget.

    Keeps paper titles + first 300 chars of each abstract only.
    Limits chunks to first 5 most relevant.

    Args:
        All the same args used to build the full prompt.

    Returns:
        A token-budget-safe prompt string.
    """
    # Truncated paper context: title + short abstract
    paper_lines = []
    for idx, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        authors = ", ".join(paper.get("authors", ["Unknown"]))[:100]
        year = paper.get("year", "N/A")
        url = paper.get("url", "")
        abstract = paper.get("abstract", "")[:300]

        paper_lines.append(
            f"### Paper {idx}: {title}\n"
            f"**Authors:** {authors} | **Year:** {year}\n"
            f"**URL:** {url}\n"
            f"**Abstract:** {abstract}...\n"
        )

    papers_context = "\n".join(paper_lines)

    # Limit chunks to top 5
    chunk_lines = []
    for idx, chunk in enumerate(chunks[:5], 1):
        text = chunk.get("text", "")[:200]
        source = chunk.get("metadata", {}).get("title", "Unknown")
        chunk_lines.append(f"**Excerpt {idx}** (from: {source}):\n{text}...\n")

    chunks_context = "\n".join(chunk_lines) if chunk_lines else "Limited excerpts available."

    return f"""Based on the following academic papers, generate a comprehensive research report.

**Research Query:** {query}
**Date:** {current_date}
**Papers Analyzed:** {paper_count}
**Mode:** {mode}

---

## Papers Found:
{papers_context}

---

## Relevant Excerpts:
{chunks_context}

---

## Report Format Instructions:
{format_instructions}

CRITICAL: Write a thorough report with 3+ paragraph Overview, 6+ Key Findings, \
4+ Research Gaps. Cite papers by title and URL.

Generate the complete report now:"""


async def _validate_and_expand(
    report: str,
    query: str,
    papers: List[Dict[str, Any]],
    llm: object,
    mode: str,
) -> str:
    """
    Validate report content depth and make a second LLM call to expand
    if the report is too shallow.

    Args:
        report: The initial report text.
        query: The research query.
        papers: Paper metadata.
        llm: LLM instance.
        mode: Report mode.

    Returns:
        The validated (and potentially expanded) report.
    """
    issues = []

    # Check Overview word count
    overview_match = _extract_section(report, "Overview")
    if overview_match:
        word_count = len(overview_match.split())
        if word_count < MIN_OVERVIEW_WORDS:
            issues.append(
                f"Overview is only {word_count} words (need {MIN_OVERVIEW_WORDS}+)"
            )

    # Check Key Findings bullet count
    findings_match = _extract_section(report, "Key Findings")
    if findings_match:
        bullet_count = (
            findings_match.count("\n-") + findings_match.count("\n*")
        )
        if bullet_count < MIN_KEY_FINDINGS:
            issues.append(
                f"Only {bullet_count} Key Findings (need {MIN_KEY_FINDINGS}+)"
            )

    # Check Research Gaps count
    gaps_match = _extract_section(report, "Research Gaps")
    if gaps_match:
        gap_count = gaps_match.count("\n-") + gaps_match.count("\n*")
        if gap_count < MIN_RESEARCH_GAPS:
            issues.append(
                f"Only {gap_count} Research Gaps (need {MIN_RESEARCH_GAPS}+)"
            )

    if not issues:
        logger.info("report_validation_passed")
        return report

    # Make a second LLM call to expand the report
    logger.info("report_expanding", issues=issues)

    paper_titles = [p.get("title", "") for p in papers[:8]]
    expansion_prompt = f"""The following research report on "{query}" needs expansion. \
Current issues: {'; '.join(issues)}.

Current report:
{report[:3000]}

Paper titles analyzed: {', '.join(paper_titles)}

Please expand this report to meet these requirements:
- Overview: minimum 3 full paragraphs ({MIN_OVERVIEW_WORDS}+ words) with synthesis
- Key Findings: minimum {MIN_KEY_FINDINGS} specific bullet points with evidence
- Research Gaps: minimum {MIN_RESEARCH_GAPS} specific open questions

Return the COMPLETE expanded report in the same markdown format. \
Keep all existing content but add more depth and detail."""

    try:
        expanded = await invoke_with_retry(
            llm, expansion_prompt, max_retries=2, base_delay=1.5
        )
        expanded = _clean_report(expanded)

        # Use the longer version
        if len(expanded) > len(report) * 0.8:
            logger.info(
                "report_expanded_successfully", new_length=len(expanded)
            )
            return expanded
        else:
            logger.info("expansion_too_short_keeping_original")
            return report

    except Exception as exc:
        logger.warning("report_expansion_failed", error=str(exc))
        return report


def _extract_section(report: str, section_name: str) -> str:
    """
    Extract the content of a named section from the markdown report.

    Args:
        report: Full report text.
        section_name: Section header to find (e.g. 'Overview').

    Returns:
        Section content string, or empty string if not found.
    """
    import re
    pattern = rf'##\s*{re.escape(section_name)}.*?\n(.*?)(?=\n##\s|\Z)'
    match = re.search(pattern, report, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


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

        citation_info = (
            f" | Citations: {citations}" if citations is not None else ""
        )

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
    report = report.strip()

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
    error_message: str = "Unknown error",
) -> str:
    """
    Generate a fallback report when the LLM fails, including the real error.

    Args:
        query: The research query.
        papers: Available paper metadata.
        date: Current date string.
        mode: Report mode.
        error_message: The actual error message from the LLM.

    Returns:
        A markdown report string with the error surfaced.
    """
    logger.warning("generating_fallback_report", error=error_message)

    paper_entries = []
    for paper in papers:
        title = paper.get("title", "Untitled")
        authors = ", ".join(paper.get("authors", ["Unknown"]))
        year = paper.get("year", "N/A")
        url = paper.get("url", "#")
        abstract = paper.get("abstract", "No abstract available.")

        paper_entries.append(
            f"- **{title}** -- {authors} ({year}) [Read Paper ->]({url})\n"
            f"  > {abstract[:200]}..."
        )

    papers_section = (
        "\n\n".join(paper_entries) if paper_entries else "No papers found."
    )

    return f"""# Research Report: {query}
**Generated:** {date} | **Papers analyzed:** {len(papers)} | **Mode:** {mode.capitalize()}

---

## Overview
This report was generated using a fallback mechanism because the LLM \
encountered an error during synthesis. The papers below were successfully \
fetched and can be reviewed manually.

**Error details:** `{error_message[:500]}`

If this error persists, try:
- Running the query again (transient API errors resolve on retry)
- Checking your Groq API key quota at https://console.groq.com
- Using fewer papers or a simpler query
- Switching LLM providers in the .env file

## Key Papers
{papers_section}

## Key Findings
- {len(papers)} papers were found matching your query "{query}"
- The papers span topics related to the query and are available for manual review
- Please review the paper abstracts above for relevant information
- Try running the query again -- the LLM error may be transient

## Research Gaps & Open Questions
- A complete analysis could not be performed due to the LLM error
- These papers still provide a useful starting point for further research
- Consider reviewing each paper individually for deeper insights

## Suggested Reading
- Review the {len(papers)} papers listed above for further exploration
- Search Google Scholar for related review papers on "{query}"

---
*Report confidence: Low -- generated via fallback due to LLM error: {error_message[:100]}*
"""