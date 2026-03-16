"""
Pydantic schemas and data models for the Personal Research Assistant Agent.

Defines request/response models, filter configurations, and enums
used across the entire backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class SortBy(str, Enum):
    """Sorting options for paper search results."""
    relevance = "relevance"
    most_recent = "most_recent"
    most_cited = "most_cited"


class Source(str, Enum):
    """Available paper source APIs."""
    arxiv = "arxiv"
    semantic_scholar = "semantic_scholar"
    both = "both"


class FilterConfig(BaseModel):
    """
    Advanced search filter configuration.

    Controls which papers are fetched and how they are sorted.
    Defaults are sensible for general use; mode_handler.py
    overrides them based on beginner/expert mode.
    """
    domain: Optional[str] = Field(
        default=None,
        description="Research domain/field filter (e.g., 'Computer Science', 'Biology')"
    )
    keywords: List[str] = Field(
        default=[],
        description="Additional keyword tags to narrow search"
    )
    year_from: Optional[int] = Field(
        default=None,
        description="Earliest publication year to include"
    )
    year_to: Optional[int] = Field(
        default=None,
        description="Latest publication year to include"
    )
    paper_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of papers to fetch (1-20)"
    )
    sort_by: SortBy = Field(
        default=SortBy.relevance,
        description="How to sort the retrieved papers"
    )
    source: Source = Field(
        default=Source.both,
        description="Which paper source(s) to query"
    )


class QueryRequest(BaseModel):
    """
    Incoming research query from the frontend.

    Contains the user's question, optional filters, and the
    display mode (expert or beginner).
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The research question or topic to investigate"
    )
    filters: FilterConfig = Field(
        default_factory=FilterConfig,
        description="Optional search filters"
    )
    mode: str = Field(
        default="expert",
        pattern="^(expert|beginner)$",
        description="Report style: 'expert' (technical) or 'beginner' (simplified)"
    )


class PaperMetadata(BaseModel):
    """Metadata for a single academic paper."""
    title: str = ""
    authors: List[str] = []
    abstract: str = ""
    url: str = ""
    year: Optional[int] = None
    source: str = ""
    citation_count: Optional[int] = None
    doi: Optional[str] = None


class ReportResponse(BaseModel):
    """
    Complete response returned after the agent finishes processing.

    Includes the markdown report, detected contradictions,
    follow-up suggestions, paper metadata, and a query ID for history.
    """
    report: str = Field(
        ...,
        description="Full markdown research report"
    )
    contradictions: List[Dict[str, Any]] = Field(
        default=[],
        description="List of detected contradictions between papers"
    )
    followups: List[str] = Field(
        default=[],
        description="3 suggested follow-up research questions"
    )
    papers: List[Dict[str, Any]] = Field(
        default=[],
        description="Metadata for all papers analyzed"
    )
    query_id: str = Field(
        ...,
        description="Unique identifier for this query (for history)"
    )


class QueryHistoryItem(BaseModel):
    """A single entry in the query history."""
    query_id: str
    query: str
    mode: str
    paper_count: int = 0
    created_at: str = ""
    has_report: bool = False


class StreamEvent(BaseModel):
    """Schema for a single SSE stream event."""
    type: str = Field(
        ...,
        description="Event type: thought, action, observation, report, followups, contradictions, done, error"
    )
    content: Any = Field(
        default="",
        description="Event payload — string, list, or dict depending on type"
    )
