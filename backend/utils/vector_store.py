"""
ChromaDB vector store operations for paper embeddings.

Provides functions to store paper chunks as embeddings, retrieve
relevant chunks via MMR (Maximal Marginal Relevance), and manage
the persistent vector database.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from utils.logger import get_logger
from utils.chunker import chunk_papers

load_dotenv()

logger = get_logger(__name__)

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "research_papers"

# Module-level client cache
_chroma_client: Optional[chromadb.PersistentClient] = None
_embedding_function: Optional[object] = None


def _get_client() -> chromadb.PersistentClient:
    """
    Get or create the ChromaDB persistent client (singleton).

    Returns:
        A ChromaDB PersistentClient instance.
    """
    global _chroma_client

    if _chroma_client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("chroma_client_init", persist_dir=CHROMA_PERSIST_DIR)

    return _chroma_client


def _get_embedding_function():
    """
    Get or create the embedding function for ChromaDB (singleton).

    Uses sentence-transformers all-MiniLM-L6-v2 via LangChain's
    HuggingFace embedding wrapper for consistency with the rest
    of the pipeline.

    Returns:
        A ChromaDB-compatible embedding function.
    """
    global _embedding_function

    if _embedding_function is None:
        from chromadb.utils import embedding_functions

        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name,
        )
        logger.info("embedding_function_init", model=model_name)

    return _embedding_function


def _get_collection() -> chromadb.Collection:
    """
    Get or create the research papers collection.

    Returns:
        The ChromaDB collection for research papers.
    """
    client = _get_client()
    ef = _get_embedding_function()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("collection_ready", name=COLLECTION_NAME, count=collection.count())
    return collection


def _generate_chunk_id(text: str, metadata: Dict[str, Any]) -> str:
    """
    Generate a deterministic ID for a chunk to avoid duplicates.

    Args:
        text: The chunk text.
        metadata: The chunk metadata.

    Returns:
        A hex digest string used as the chunk's ID in ChromaDB.
    """
    unique_string = f"{metadata.get('title', '')}|{metadata.get('chunk_index', 0)}|{text[:100]}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


def store_papers(
    papers: List[Dict[str, Any]],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> int:
    """
    Chunk papers and store their embeddings in ChromaDB.

    Deduplicates by chunk ID so re-indexing the same paper is safe.

    Args:
        papers: List of paper dicts with title, abstract, authors, url, year.
        chunk_size: Token limit per chunk.
        chunk_overlap: Token overlap between consecutive chunks.

    Returns:
        Number of new chunks added.
    """
    if not papers:
        logger.warning("store_papers_empty")
        return 0

    chunks = chunk_papers(papers, chunk_size, chunk_overlap)
    if not chunks:
        logger.warning("store_papers_no_chunks")
        return 0

    collection = _get_collection()

    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for chunk in chunks:
        chunk_id = _generate_chunk_id(chunk["text"], chunk["metadata"])

        # Convert metadata values to ChromaDB-compatible types
        safe_metadata = {}
        for key, value in chunk["metadata"].items():
            if value is None:
                safe_metadata[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                safe_metadata[key] = value
            else:
                safe_metadata[key] = str(value)

        documents.append(chunk["text"])
        metadatas.append(safe_metadata)
        ids.append(chunk_id)

    try:
        # upsert to handle duplicates gracefully
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(
            "papers_stored",
            chunks_upserted=len(documents),
            collection_total=collection.count(),
        )
        return len(documents)
    except Exception as exc:
        logger.error("store_papers_failed", error=str(exc))
        raise


def search_similar(
    query: str,
    n_results: int = 10,
    where_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Search for chunks similar to the query using cosine similarity.

    Args:
        query: The search query text.
        n_results: Number of results to return.
        where_filter: Optional ChromaDB metadata filter.

    Returns:
        List of result dicts with 'text', 'metadata', and 'distance' keys.
    """
    collection = _get_collection()

    try:
        query_params = {
            "query_texts": [query],
            "n_results": min(n_results, collection.count()) if collection.count() > 0 else n_results,
        }
        if where_filter:
            query_params["where"] = where_filter

        results = collection.query(**query_params)
    except Exception as exc:
        logger.error("search_failed", error=str(exc))
        return []

    if not results or not results.get("documents"):
        return []

    output: List[Dict[str, Any]] = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
    distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)

    for doc, meta, dist in zip(documents, metadatas, distances):
        output.append({
            "text": doc,
            "metadata": meta,
            "distance": dist,
        })

    logger.info("search_complete", query=query[:60], results=len(output))
    return output


def mmr_search(
    query: str,
    n_results: int = 10,
    diversity_factor: float = 0.3,
    where_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve chunks using Maximal Marginal Relevance for diversity.

    First retrieves more candidates than needed, then re-ranks them
    to balance relevance with diversity (avoiding near-duplicate results).

    Args:
        query: The search query text.
        n_results: Desired number of diverse results.
        diversity_factor: 0.0 = pure relevance, 1.0 = pure diversity.
        where_filter: Optional ChromaDB metadata filter.

    Returns:
        List of diverse result dicts.
    """
    # Fetch extra candidates for MMR selection
    candidate_count = min(n_results * 3, 30)
    candidates = search_similar(query, n_results=candidate_count, where_filter=where_filter)

    if not candidates:
        return []

    if len(candidates) <= n_results:
        return candidates

    # Simple MMR: greedily select diverse results
    selected: List[Dict[str, Any]] = [candidates[0]]
    remaining = candidates[1:]

    while len(selected) < n_results and remaining:
        best_score = -1.0
        best_idx = 0

        for idx, candidate in enumerate(remaining):
            # Relevance score (inverse distance — lower distance = more relevant)
            relevance = 1.0 / (1.0 + candidate["distance"])

            # Diversity score: max similarity to already-selected items
            max_similarity = 0.0
            for sel in selected:
                # Use text overlap as a rough similarity proxy
                similarity = _text_overlap(candidate["text"], sel["text"])
                max_similarity = max(max_similarity, similarity)

            # MMR score: balance relevance and diversity
            mmr_score = (1.0 - diversity_factor) * relevance - diversity_factor * max_similarity

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(remaining.pop(best_idx))

    logger.info(
        "mmr_search_complete",
        query=query[:60],
        candidates=len(candidates),
        selected=len(selected),
    )
    return selected


def _text_overlap(text_a: str, text_b: str) -> float:
    """
    Compute a rough Jaccard similarity between two texts using word sets.

    Args:
        text_a: First text.
        text_b: Second text.

    Returns:
        Float between 0.0 and 1.0 indicating similarity.
    """
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def clear_collection() -> None:
    """
    Delete all documents from the research papers collection.

    Useful for resetting the vector store during development.
    """
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("collection_cleared", name=COLLECTION_NAME)
    except Exception as exc:
        logger.warning("collection_clear_failed", error=str(exc))


def get_collection_stats() -> Dict[str, Any]:
    """
    Get statistics about the current vector store collection.

    Returns:
        Dictionary with collection name and document count.
    """
    try:
        collection = _get_collection()
        return {
            "collection": COLLECTION_NAME,
            "document_count": collection.count(),
            "persist_dir": CHROMA_PERSIST_DIR,
        }
    except Exception as exc:
        logger.error("collection_stats_failed", error=str(exc))
        return {
            "collection": COLLECTION_NAME,
            "document_count": 0,
            "error": str(exc),
        }
