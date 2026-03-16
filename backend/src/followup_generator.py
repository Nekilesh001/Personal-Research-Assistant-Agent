"""
Follow-up question generator.

After generating a research report, this module produces 3 clickable
follow-up questions that allow users to dive deeper into related topics.
"""

from typing import List, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


async def generate_followups(
    query: str,
    report: str,
    papers: List[Dict[str, Any]],
    llm: object,
    mode: str = "expert",
) -> List[str]:
    """
    Generate 3 follow-up research questions based on the completed report.

    Questions are designed to help the user explore related areas,
    dive deeper into specific findings, or investigate research gaps
    identified in the report.

    Args:
        query: The original research query.
        report: The generated markdown report.
        papers: List of paper metadata used in the report.
        llm: A LangChain LLM instance.
        mode: 'expert' or 'beginner' — affects question complexity.

    Returns:
        List of exactly 3 follow-up question strings.
    """
    logger.info("followup_generation_start", query=query[:80], mode=mode)

    # Build a concise summary of the papers for context
    paper_titles = [p.get("title", "Untitled") for p in papers[:10]]
    papers_context = "\n".join(f"- {title}" for title in paper_titles)

    style_guide = _get_style_guide(mode)

    prompt = f"""Based on the following research query and the papers that were analyzed, 
generate exactly 3 follow-up research questions that would help the user explore further.

**Original Query:** {query}

**Papers Analyzed:**
{papers_context}

**Report Excerpt (first 500 chars):**
{report[:500]}...

{style_guide}

Rules:
- Generate EXACTLY 3 questions, one per line
- Each question should explore a DIFFERENT angle or sub-topic
- Questions should be self-contained (a new search query, not referencing "the papers above")
- Questions should be specific enough to yield good search results
- Do NOT number them or add bullet points — just the question text, one per line
- Each question should be between 10 and 100 characters

Generate 3 follow-up questions now:"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        followups = _parse_followups(content)

        logger.info("followup_generation_success", count=len(followups))
        return followups

    except Exception as exc:
        logger.error("followup_generation_failed", error=str(exc))
        return _generate_fallback_followups(query)


def _get_style_guide(mode: str) -> str:
    """
    Get mode-specific instructions for follow-up question style.

    Args:
        mode: 'expert' or 'beginner'.

    Returns:
        Style instruction string.
    """
    if mode.lower().strip() == "beginner":
        return """**Style:** Questions should be in plain, simple English. 
Avoid jargon. Frame questions as a curious learner would ask them.
Example: "How do large language models actually learn from text?"
"""
    else:
        return """**Style:** Questions should be technically precise and specific.
Use academic terminology and focus on methodological or theoretical depth.
Example: "What are the comparative advantages of transformer vs. diffusion architectures for sequence modeling?"
"""


def _parse_followups(response_text: str) -> List[str]:
    """
    Parse the LLM response into a list of follow-up questions.

    Args:
        response_text: Raw LLM response text.

    Returns:
        List of exactly 3 follow-up question strings.
    """
    lines = response_text.strip().split("\n")

    questions = []
    for line in lines:
        # Clean up the line
        cleaned = line.strip()
        # Remove common prefixes (numbers, bullets, dashes)
        cleaned = cleaned.lstrip("0123456789.-•*) ")
        cleaned = cleaned.strip()

        # Only keep lines that look like questions (non-empty, reasonable length)
        if cleaned and len(cleaned) >= 10 and len(cleaned) <= 200:
            # Ensure it ends with a question mark
            if not cleaned.endswith("?"):
                cleaned += "?"
            questions.append(cleaned)

    # Return exactly 3 (pad or trim as needed)
    if len(questions) >= 3:
        return questions[:3]
    elif questions:
        # Pad with generic questions if we got fewer than 3
        return questions + _generate_fallback_followups("")[:3 - len(questions)]
    else:
        return _generate_fallback_followups("")


def _generate_fallback_followups(query: str) -> List[str]:
    """
    Generate generic fallback follow-up questions when LLM fails.

    Args:
        query: The original query (used to contextualize fallbacks).

    Returns:
        List of 3 generic follow-up questions.
    """
    if query:
        return [
            f"What are the latest advancements in {query}?",
            f"What are the main challenges and limitations in {query}?",
            f"How is {query} being applied in real-world scenarios?",
        ]
    else:
        return [
            "What are the latest trends in this research area?",
            "What methodological approaches are being used?",
            "What are the practical applications of this research?",
        ]
