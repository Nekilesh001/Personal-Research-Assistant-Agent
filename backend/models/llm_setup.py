"""
LLM provider setup with automatic fallback chain.

Priority order: Gemini → OpenAI → Ollama.
If the configured provider's API key is missing or fails,
the system automatically falls back to the next available provider.
"""

import os
from typing import Optional, Tuple

from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


def get_llm(
    temperature: float = 0.3,
    streaming: bool = True,
) -> object:
    """
    Initialize and return an LLM instance based on environment configuration.

    Tries providers in order: gemini → openai → ollama.
    Falls back automatically if a provider's key is missing.

    Args:
        temperature: LLM sampling temperature (0.0 = deterministic, 1.0 = creative).
        streaming: Whether to enable streaming token output.

    Returns:
        A LangChain LLM instance ready for use.

    Raises:
        RuntimeError: If no LLM provider could be initialized.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    logger.info("llm_init_start", provider=provider)

    # Define the fallback chain based on the preferred provider
    provider_chain = _build_fallback_chain(provider)

    last_error: Optional[Exception] = None
    for candidate in provider_chain:
        try:
            llm = _init_provider(candidate, temperature, streaming)
            if llm is not None:
                logger.info("llm_init_success", provider=candidate)
                return llm
        except Exception as exc:
            logger.warning(
                "llm_init_failed",
                provider=candidate,
                error=str(exc),
            )
            last_error = exc

    error_msg = (
        "No LLM provider could be initialized. "
        "Please set at least one of: GOOGLE_API_KEY, OPENAI_API_KEY, "
        "or ensure Ollama is running at OLLAMA_BASE_URL. "
        f"Last error: {last_error}"
    )
    logger.error("llm_init_all_failed", error=error_msg)
    raise RuntimeError(error_msg)


def get_embeddings() -> object:
    """
    Initialize the sentence-transformers embedding model.

    Uses all-MiniLM-L6-v2 which runs locally and requires no API key.

    Returns:
        A LangChain-compatible embedding instance.
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings

    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    logger.info("embeddings_init", model=model_name)

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("embeddings_init_success", model=model_name)
    return embeddings


def _build_fallback_chain(preferred: str) -> list:
    """
    Build the provider fallback chain starting with the preferred provider.

    Args:
        preferred: The preferred LLM provider name.

    Returns:
        Ordered list of provider names to try.
    """
    all_providers = ["gemini", "openai", "ollama"]

    if preferred in all_providers:
        all_providers.remove(preferred)
        return [preferred] + all_providers

    logger.warning("unknown_provider", provider=preferred, fallback="gemini")
    return all_providers


def _init_provider(
    provider: str,
    temperature: float,
    streaming: bool,
) -> Optional[object]:
    """
    Attempt to initialize a specific LLM provider.

    Args:
        provider: Provider name ('gemini', 'openai', or 'ollama').
        temperature: Sampling temperature.
        streaming: Whether to enable streaming.

    Returns:
        An LLM instance, or None if the provider's key is missing.
    """
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            logger.info("gemini_no_key", reason="GOOGLE_API_KEY not set")
            return None

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            google_api_key=api_key,
            temperature=temperature,
            streaming=streaming,
            convert_system_message_to_human=True,
        )

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            logger.info("openai_no_key", reason="OPENAI_API_KEY not set")
            return None

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=api_key,
            temperature=temperature,
            streaming=streaming,
        )

    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=base_url,
            temperature=temperature,
        )

    else:
        logger.warning("unknown_provider_skip", provider=provider)
        return None
