"""
Semantic text chunking for academic paper abstracts and content.

Splits text into overlapping chunks suitable for embedding and
storage in ChromaDB. Uses tiktoken for accurate token counting
to prevent LLM context overflow.

Includes:
  - 500-token cap per paper chunk for embedding
  - truncate_for_llm() helper to keep prompts under budget
"""

import re
from typing import List, Dict, Any

import tiktoken
from utils.logger import get_logger

logger = get_logger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 500         # tokens per chunk (capped for embedding)
DEFAULT_CHUNK_OVERLAP = 64       # overlapping tokens between chunks
DEFAULT_ENCODING = "cl100k_base"  # tiktoken encoding (GPT-4/3.5 compatible)
MAX_CHUNK_TOKENS = 500           # hard cap per paper chunk before embedding


def get_token_count(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """
    Count the number of tokens in a text string.

    Args:
        text: The input text to count tokens for.
        encoding_name: The tiktoken encoding to use.

    Returns:
        Number of tokens in the text.
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as exc:
        logger.warning("token_count_fallback", error=str(exc))
        # Rough fallback: ~4 characters per token
        return len(text) // 4


def truncate_text_to_tokens(
    text: str,
    max_tokens: int,
    encoding_name: str = DEFAULT_ENCODING,
) -> str:
    """
    Truncate text to a maximum number of tokens.

    Args:
        text: The input text.
        max_tokens: Maximum tokens to keep.
        encoding_name: The tiktoken encoding.

    Returns:
        Truncated text that fits within max_tokens.
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens])
    except Exception:
        # Fallback: character-based approximation
        approx_chars = max_tokens * 4
        return text[:approx_chars]


def truncate_for_llm(
    papers: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    max_tokens: int = 28000,
) -> tuple:
    """
    Truncate papers and chunks to fit within an LLM token budget.

    Strategy: if total context exceeds max_tokens, keep only
    paper titles + first 300 chars of each abstract, and limit
    chunks to the top 5.

    Args:
        papers: List of paper metadata dicts.
        chunks: List of chunk dicts.
        max_tokens: Maximum total tokens for the context.

    Returns:
        Tuple of (truncated_papers, truncated_chunks).
    """
    # Estimate total tokens from papers
    total_paper_tokens = 0
    for paper in papers:
        abstract = paper.get("abstract", "")
        title = paper.get("title", "")
        total_paper_tokens += get_token_count(f"{title} {abstract}")

    # Estimate total tokens from chunks
    total_chunk_tokens = sum(
        get_token_count(c.get("text", "")) for c in chunks
    )

    total = total_paper_tokens + total_chunk_tokens
    logger.info(
        "truncation_check",
        total_tokens=total,
        max_tokens=max_tokens,
        paper_tokens=total_paper_tokens,
        chunk_tokens=total_chunk_tokens,
    )

    if total <= max_tokens:
        return papers, chunks

    logger.warning("truncating_for_llm", total=total, max=max_tokens)

    # Truncate papers: keep titles + first 300 chars of abstract
    truncated_papers = []
    for paper in papers:
        truncated = dict(paper)
        abstract = truncated.get("abstract", "")
        if len(abstract) > 300:
            truncated["abstract"] = abstract[:300] + "..."
        truncated_papers.append(truncated)

    # Limit chunks to top 5
    truncated_chunks = chunks[:5]
    for chunk in truncated_chunks:
        text = chunk.get("text", "")
        if get_token_count(text) > 200:
            chunk["text"] = truncate_text_to_tokens(text, 200)

    return truncated_papers, truncated_chunks


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    encoding_name: str = DEFAULT_ENCODING,
) -> List[str]:
    """
    Split text into overlapping chunks based on token count.

    Uses sentence boundaries for cleaner splits when possible.
    Each chunk is capped at MAX_CHUNK_TOKENS (500 tokens).

    Args:
        text: The input text to split.
        chunk_size: Maximum tokens per chunk.
        chunk_overlap: Number of overlapping tokens between consecutive chunks.
        encoding_name: The tiktoken encoding to use.

    Returns:
        List of text chunks, each within the token budget.
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # Enforce the hard cap
    effective_chunk_size = min(chunk_size, MAX_CHUNK_TOKENS)

    total_tokens = get_token_count(text, encoding_name)

    # If text fits in a single chunk, return as-is
    if total_tokens <= effective_chunk_size:
        return [text]

    # Split into sentences for cleaner boundaries
    sentences = _split_into_sentences(text)

    chunks: List[str] = []
    current_chunk_sentences: List[str] = []
    current_token_count = 0

    for sentence in sentences:
        sentence_tokens = get_token_count(sentence, encoding_name)

        # If a single sentence exceeds chunk_size, force-split it
        if sentence_tokens > effective_chunk_size:
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_token_count = 0

            sub_chunks = _force_split(sentence, effective_chunk_size, encoding_name)
            chunks.extend(sub_chunks)
            continue

        # Check if adding this sentence exceeds chunk_size
        if current_token_count + int(sentence_tokens) > effective_chunk_size:
            chunks.append(" ".join(current_chunk_sentences))

            # Compute overlap
            overlap_sentences: List[str] = []
            overlap_tokens = 0
            for prev_sentence in reversed(current_chunk_sentences):
                prev_tokens = get_token_count(prev_sentence, encoding_name)
                if overlap_tokens + prev_tokens > chunk_overlap:
                    break
                overlap_sentences.insert(0, prev_sentence)
                overlap_tokens += prev_tokens

            current_chunk_sentences = overlap_sentences + [sentence]
            current_token_count = overlap_tokens + sentence_tokens
        else:
            current_chunk_sentences.append(sentence)
            current_token_count += int(sentence_tokens)

    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    logger.info(
        "text_chunked",
        total_tokens=total_tokens,
        num_chunks=len(chunks),
        chunk_size=effective_chunk_size,
    )
    return chunks


def chunk_papers(
    papers: List[Dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Chunk a list of paper abstracts, preserving metadata for each chunk.

    Each chunk retains the source paper's title, authors, URL, and year
    as metadata, making it traceable during retrieval. Each chunk is
    capped at 500 tokens max.

    Args:
        papers: List of paper dicts with at least 'title' and 'abstract' fields.
        chunk_size: Maximum tokens per chunk.
        chunk_overlap: Overlapping tokens between chunks.

    Returns:
        List of dicts with 'text', 'metadata' keys for each chunk.
    """
    all_chunks: List[Dict[str, Any]] = []

    # Enforce the hard cap
    effective_chunk_size = min(chunk_size, MAX_CHUNK_TOKENS)

    for paper in papers:
        abstract = paper.get("abstract", "")
        title = paper.get("title", "Untitled")

        if not abstract:
            logger.warning("paper_no_abstract", title=title)
            continue

        # Prepend title for context in each chunk
        full_text = f"{title}. {abstract}"

        # Truncate if the full text exceeds 500 tokens before chunking
        if get_token_count(full_text) > MAX_CHUNK_TOKENS:
            full_text = truncate_text_to_tokens(full_text, MAX_CHUNK_TOKENS)

        text_chunks = chunk_text(full_text, effective_chunk_size, chunk_overlap)

        for idx, chunk in enumerate(text_chunks):
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    "title": title,
                    "authors": ", ".join(paper.get("authors", [])),
                    "url": paper.get("url", ""),
                    "year": str(paper.get("year", "")),
                    "source": paper.get("source", "unknown"),
                    "chunk_index": str(idx),
                    "total_chunks": str(len(text_chunks)),
                },
            })

    logger.info(
        "papers_chunked",
        num_papers=len(papers),
        total_chunks=len(all_chunks),
    )
    return all_chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex-based heuristics.

    Args:
        text: Input text to split.

    Returns:
        List of sentence strings.
    """
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def _force_split(
    text: str,
    chunk_size: int,
    encoding_name: str,
) -> List[str]:
    """
    Force-split a long text that exceeds chunk_size by token slicing.

    Args:
        text: The text to split.
        chunk_size: Maximum tokens per chunk.
        encoding_name: The tiktoken encoding.

    Returns:
        List of text chunks, each within the token budget.
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
    except Exception:
        approx_chars = chunk_size * 4
        return [text[i:i + approx_chars] for i in range(0, len(text), approx_chars)]

    chunks: List[str] = []
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text_decoded = encoding.decode(chunk_tokens)
        chunks.append(chunk_text_decoded)

    return chunks
