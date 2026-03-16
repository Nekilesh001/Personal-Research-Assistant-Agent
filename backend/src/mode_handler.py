"""
Mode handler for expert vs beginner prompt switching.

Provides different system prompts and default filter configurations
based on the selected mode. Expert mode uses technical language
and citations; beginner mode uses simple language and analogies.
"""

from typing import Dict, Any, Tuple

from models.schemas import FilterConfig, SortBy
from utils.logger import get_logger

logger = get_logger(__name__)


# System prompt templates
EXPERT_SYSTEM_PROMPT = """You are an expert research analyst with deep knowledge across scientific domains. 
Your task is to analyze academic papers and produce a comprehensive, technically rigorous research report.

Guidelines:
- Use precise technical terminology appropriate for the field
- Include specific methodological details when relevant
- Cite papers using [Author et al., Year] format with direct links
- Discuss statistical significance, effect sizes, and confidence intervals when mentioned
- Compare and contrast methodologies across papers
- Identify methodological strengths and limitations
- Note when papers contradict each other — explain the nature of the disagreement
- Highlight research gaps and suggest future directions
- Use field-specific jargon where appropriate (readers are experts)
- Structure your analysis with clear logical flow
- Quantify findings where possible

When handling vague queries:
1. First expand the query into 2-3 specific search terms
2. Search for papers across multiple sources
3. Prioritize recent, highly-cited papers
4. Synthesize findings into a coherent narrative

Always include paper URLs so readers can access the original sources.
Always identify open research questions and gaps in the literature."""

BEGINNER_SYSTEM_PROMPT = """You are a friendly research educator who explains complex academic topics in plain English.
Your task is to analyze academic papers and produce an easy-to-understand research report.

Guidelines:
- Use simple, everyday language — avoid jargon
- When you must use a technical term, explain it immediately with an analogy
  Example: "Neural networks (think of them like a brain made of math)"
- Use relatable analogies to explain complex concepts
- Focus on the "what" and "why it matters" rather than methodological details
- Mention paper titles but keep citations informal and non-intimidating
- Use examples from everyday life to illustrate findings
- Highlight practical implications — how does this affect regular people?
- Keep paragraphs short (2-3 sentences max)
- Use bullet points and numbered lists for clarity
- Add a "Key Takeaway" at the end of each section
- Avoid abbreviations; spell everything out
- Use encouraging, engaging tone — make science exciting!

When handling vague queries:
1. First expand the query into 2-3 specific search terms
2. Search for papers across multiple sources
3. Focus on the most impactful and understandable papers
4. Present findings as a story, not a catalog

Always include paper links for curious readers who want to dive deeper.
Always end with "What This Means For You" — practical takeaways."""


# Default filter configurations per mode
EXPERT_DEFAULTS = {
    "year_offset": 5,       # last 5 years
    "paper_count": 10,
    "sort_by": SortBy.most_cited,
}

BEGINNER_DEFAULTS = {
    "year_offset": 2,       # last 2 years
    "paper_count": 5,
    "sort_by": SortBy.relevance,
}


def get_system_prompt(mode: str) -> str:
    """
    Get the appropriate system prompt based on the selected mode.

    Args:
        mode: Either 'expert' or 'beginner'.

    Returns:
        The system prompt string for the selected mode.
    """
    mode = mode.lower().strip()

    if mode == "beginner":
        logger.info("mode_selected", mode="beginner")
        return BEGINNER_SYSTEM_PROMPT
    else:
        logger.info("mode_selected", mode="expert")
        return EXPERT_SYSTEM_PROMPT


def apply_mode_defaults(
    filters: FilterConfig,
    mode: str,
) -> FilterConfig:
    """
    Apply mode-specific default values to filters that weren't explicitly set.

    Expert mode: last 5 years, 10 papers, sorted by citations.
    Beginner mode: last 2 years, 5 papers, sorted by relevance.

    Args:
        filters: The user-provided filter configuration.
        mode: Either 'expert' or 'beginner'.

    Returns:
        Updated FilterConfig with mode-appropriate defaults.
    """
    mode = mode.lower().strip()
    defaults = BEGINNER_DEFAULTS if mode == "beginner" else EXPERT_DEFAULTS

    from datetime import datetime
    current_year = datetime.now().year

    # Only apply defaults if the user didn't explicitly set values
    updated_data = filters.model_dump()

    if filters.year_from is None:
        updated_data["year_from"] = current_year - defaults["year_offset"]
        logger.info("mode_default_applied", field="year_from", value=updated_data["year_from"])

    if filters.year_to is None:
        updated_data["year_to"] = current_year
        logger.info("mode_default_applied", field="year_to", value=updated_data["year_to"])

    # Only override paper_count if it's still at the general default (5)
    if filters.paper_count == 5 and mode == "expert":
        updated_data["paper_count"] = defaults["paper_count"]
        logger.info("mode_default_applied", field="paper_count", value=defaults["paper_count"])

    # Only override sort_by if it's still at the general default (relevance)
    if filters.sort_by == SortBy.relevance and mode == "expert":
        updated_data["sort_by"] = defaults["sort_by"]
        logger.info("mode_default_applied", field="sort_by", value=defaults["sort_by"].value)

    updated_filters = FilterConfig(**updated_data)

    logger.info(
        "mode_defaults_complete",
        mode=mode,
        year_range=f"{updated_filters.year_from}-{updated_filters.year_to}",
        paper_count=updated_filters.paper_count,
        sort_by=updated_filters.sort_by.value,
    )

    return updated_filters


def get_report_format_instructions(mode: str) -> str:
    """
    Get mode-specific instructions for report formatting.

    Args:
        mode: Either 'expert' or 'beginner'.

    Returns:
        Markdown formatting instructions for the report generator.
    """
    if mode.lower().strip() == "beginner":
        return """
Format the report as follows:

# Research Report: {query}
**Generated:** {date} | **Papers analyzed:** {count} | **Mode:** Beginner-Friendly

---

## 🔍 What's This All About?
2-3 paragraphs explaining the topic in simple terms with analogies.

## 📚 Key Papers We Found
For each paper:
- **Title** — Authors (Year) [Read Paper →](url)
  > One sentence explaining the paper in plain English

## 💡 What Scientists Discovered
Bullet points of the most important findings, explained simply.

## ❓ What We Still Don't Know
Open questions explained in accessible language.

## 📖 Want to Learn More?
3 recommended next steps for curious readers.

---
*How confident are we? High/Medium/Low — based on {count} papers*
"""
    else:
        return """
Format the report as follows:

# Research Report: {query}
**Generated:** {date} | **Papers analyzed:** {count} | **Mode:** Expert

---

## Overview
2-3 paragraph synthesis of the field based on fetched papers.

## Key Papers
For each paper:
- **Title** — Authors (Year) [Read Paper →](url)
  > One sentence summary

## Key Findings
Bullet points of the most important findings across all papers.

## Research Gaps & Open Questions
What is still unsolved, what the papers suggest needs more work.

## Suggested Reading
3 recommended follow-up papers or topics.

---
*Report confidence: High/Medium/Low — based on number of sources*
"""
