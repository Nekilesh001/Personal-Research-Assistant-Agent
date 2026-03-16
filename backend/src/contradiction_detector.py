"""
Contradiction detector for research papers.

Analyzes paper abstracts and findings to identify conflicting
conclusions, highlight disagreements, and explain the nature
of each contradiction.
"""

from typing import List, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


async def detect_contradictions(
    papers: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    llm: object,
) -> List[Dict[str, Any]]:
    """
    Detect contradictions and conflicting findings across papers.

    Uses the LLM to compare paper abstracts and identify where
    different papers reach opposing or conflicting conclusions.

    Args:
        papers: List of paper metadata dictionaries.
        chunks: Relevant text chunks from the vector store.
        llm: A LangChain LLM instance.

    Returns:
        List of contradiction dictionaries, each containing:
          - paper_a: title of the first paper
          - paper_b: title of the second paper
          - description: explanation of the contradiction
          - severity: 'minor', 'moderate', or 'major'
    """
    if len(papers) < 2:
        logger.info("contradiction_skip", reason="fewer than 2 papers")
        return []

    logger.info("contradiction_detection_start", num_papers=len(papers))

    # Build a summary of all papers for comparison
    papers_summary = _build_comparison_context(papers)

    prompt = f"""You are an expert at identifying contradictions and conflicting findings in academic research.

Analyze the following papers and identify ANY contradictions, disagreements, or conflicting conclusions between them.

{papers_summary}

For each contradiction found, respond with EXACTLY this format (one per contradiction):

CONTRADICTION:
PAPER_A: [exact title of first paper]
PAPER_B: [exact title of second paper]
DESCRIPTION: [clear explanation of how these papers contradict each other]
SEVERITY: [minor/moderate/major]
END

Rules:
- Only report GENUINE contradictions (different conclusions on the same topic)
- Do NOT report differences in scope or methodology as contradictions
- Do NOT report complementary findings as contradictions
- Severity guide:
  - minor: different emphasis or nuance on the same finding
  - moderate: conflicting results that could be explained by methodology differences
  - major: fundamentally opposing conclusions on the same research question
- If no contradictions exist, respond with: NO_CONTRADICTIONS_FOUND

Analyze now:"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        contradictions = _parse_contradictions(content, papers)

        logger.info(
            "contradiction_detection_complete",
            contradictions_found=len(contradictions),
        )
        return contradictions

    except Exception as exc:
        logger.error("contradiction_detection_failed", error=str(exc))
        return []


def _build_comparison_context(papers: List[Dict[str, Any]]) -> str:
    """
    Build a formatted comparison context from paper metadata.

    Args:
        papers: List of paper metadata dictionaries.

    Returns:
        Formatted string for LLM comparison.
    """
    lines = []
    for idx, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        authors = ", ".join(paper.get("authors", ["Unknown"]))
        year = paper.get("year", "N/A")
        abstract = paper.get("abstract", "No abstract available.")

        lines.append(
            f"### Paper {idx}: {title}\n"
            f"**Authors:** {authors} ({year})\n"
            f"**Abstract:** {abstract}\n"
        )

    return "\n".join(lines)


def _parse_contradictions(
    response_text: str,
    papers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Parse the LLM response into structured contradiction objects.

    Args:
        response_text: Raw LLM response text.
        papers: List of paper metadata for URL lookup.

    Returns:
        List of contradiction dictionaries.
    """
    if "NO_CONTRADICTIONS_FOUND" in response_text.upper():
        return []

    contradictions: List[Dict[str, Any]] = []

    # Split by CONTRADICTION: marker
    blocks = response_text.split("CONTRADICTION:")

    for block in blocks[1:]:  # Skip first (preamble text)
        contradiction = _parse_single_contradiction(block, papers)
        if contradiction:
            contradictions.append(contradiction)

    return contradictions


def _parse_single_contradiction(
    block: str,
    papers: List[Dict[str, Any]],
) -> Dict[str, Any] | None:
    """
    Parse a single contradiction block from the LLM response.

    Args:
        block: Text block for one contradiction.
        papers: Paper list for URL lookup.

    Returns:
        Contradiction dict, or None if parsing failed.
    """
    lines = block.strip().split("\n")

    paper_a = ""
    paper_b = ""
    description = ""
    severity = "moderate"

    for line in lines:
        line = line.strip()
        if line.startswith("PAPER_A:"):
            paper_a = line.replace("PAPER_A:", "").strip()
        elif line.startswith("PAPER_B:"):
            paper_b = line.replace("PAPER_B:", "").strip()
        elif line.startswith("DESCRIPTION:"):
            description = line.replace("DESCRIPTION:", "").strip()
        elif line.startswith("SEVERITY:"):
            raw_severity = line.replace("SEVERITY:", "").strip().lower()
            if raw_severity in ("minor", "moderate", "major"):
                severity = raw_severity
        elif line == "END":
            break

    if not paper_a or not paper_b or not description:
        return None

    # Look up URLs for the papers
    url_a = _find_paper_url(paper_a, papers)
    url_b = _find_paper_url(paper_b, papers)

    return {
        "paper_a": paper_a,
        "paper_b": paper_b,
        "url_a": url_a,
        "url_b": url_b,
        "description": description,
        "severity": severity,
    }


def _find_paper_url(title: str, papers: List[Dict[str, Any]]) -> str:
    """
    Find the URL for a paper by title (fuzzy match).

    Args:
        title: The paper title to search for.
        papers: List of paper metadata.

    Returns:
        The paper's URL, or empty string if not found.
    """
    title_lower = title.lower().strip()

    for paper in papers:
        paper_title = paper.get("title", "").lower().strip()
        # Exact match or significant overlap
        if paper_title == title_lower or title_lower in paper_title or paper_title in title_lower:
            return paper.get("url", "")

    return ""
