"""
Semantic text chunking for academic paper abstracts and content.

Splits text into overlapping chunks suitable for embedding and
storage in ChromaDB. Uses tiktoken for accurate token counting
to prevent LLM context overflow.
"""

import re
from typing import List, Dict, Any

import tiktoken
from utils.logger import get_logger

logger = get_logger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 512        # tokens per chunk
DEFAULT_CHUNK_OVERLAP = 64      # overlapping tokens between chunks
DEFAULT_ENCODING = "cl100k_base"  # tiktoken encoding (GPT-4/3.5 compatible)


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


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    encoding_name: str = DEFAULT_ENCODING,
) -> List[str]:
    """
    Split text into overlapping chunks based on token count.

    Uses sentence boundaries for cleaner splits when possible.

    Args:
        text: The input text to split.
        chunk_size: Maximum tokens per chunk.
        chunk_overlap: Number of overlapping tokens between consecutive chunks.
        encoding_name: The tiktoken encoding to use.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    total_tokens = get_token_count(text, encoding_name)

    # If text fits in a single chunk, return as-is
    if total_tokens <= chunk_size:
        return [text]

    # Split into sentences for cleaner boundaries
    sentences = _split_into_sentences(text)

    chunks: List[str] = []
    current_chunk_sentences: List[str] = []
    current_token_count = 0

    for sentence in sentences:
        sentence_tokens = get_token_count(sentence, encoding_name)

        # If a single sentence exceeds chunk_size, force-split it
        if sentence_tokens > chunk_size:
            # Flush current chunk first
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_token_count = 0

            # Force-split the long sentence by characters
            sub_chunks = _force_split(sentence, chunk_size, encoding_name)
            chunks.extend(sub_chunks)
            continue

        # Check if adding this sentence exceeds chunk_size
        if current_token_count + sentence_tokens > chunk_size:
            # Save current chunk
            chunks.append(" ".join(current_chunk_sentences))

            # Compute overlap: keep trailing sentences that fit in overlap budget
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
            current_token_count += sentence_tokens

    # Don't forget the last chunk
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    logger.info(
        "text_chunked",
        total_tokens=total_tokens,
        num_chunks=len(chunks),
        chunk_size=chunk_size,
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
    as metadata, making it traceable during retrieval.

    Args:
        papers: List of paper dicts with at least 'title' and 'abstract' fields.
        chunk_size: Maximum tokens per chunk.
        chunk_overlap: Overlapping tokens between chunks.

    Returns:
        List of dicts with 'text', 'metadata' keys for each chunk.
    """
    all_chunks: List[Dict[str, Any]] = []

    for paper in papers:
        abstract = paper.get("abstract", "")
        title = paper.get("title", "Untitled")

        if not abstract:
            logger.warning("paper_no_abstract", title=title)
            continue

        # Prepend title for context in each chunk
        full_text = f"{title}. {abstract}"
        text_chunks = chunk_text(full_text, chunk_size, chunk_overlap)

        for idx, chunk in enumerate(text_chunks):
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    "title": title,
                    "authors": ", ".join(paper.get("authors", [])),
                    "url": paper.get("url", ""),
                    "year": paper.get("year"),
                    "source": paper.get("source", "unknown"),
                    "chunk_index": idx,
                    "total_chunks": len(text_chunks),
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
    # Split on sentence-ending punctuation followed by whitespace
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    # Filter out empty strings
    return [s.strip() for s in sentences if s.strip()]


def _force_split(
    text: str,
    chunk_size: int,
    encoding_name: str,
) -> List[str]:
    """
    Force-split a long text that exceeds chunk_size by character slicing.

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
        # Fallback: rough character-based splitting
        approx_chars = chunk_size * 4
        return [text[i:i + approx_chars] for i in range(0, len(text), approx_chars)]

    chunks: List[str] = []
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

    return chunks
