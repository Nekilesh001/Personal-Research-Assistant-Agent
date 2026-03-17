"""
LLM provider setup — Groq is the PRIMARY provider.
Priority chain: groq → openai → ollama (Gemini removed entirely).

Includes:
  - get_llm() with Groq-first fallback chain
  - invoke_with_retry() for resilient LLM calls with exponential backoff
  - test_llm_connection() for the /api/test-llm endpoint
"""

import os
import asyncio
import time
from typing import Optional, Any

from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Provider priority order — Gemini is removed
PROVIDER_CHAIN = ["groq", "openai", "ollama"]


def get_llm(
    temperature: float = 0.3,
    streaming: bool = True,
) -> object:
    """
    Initialize and return an LLM instance based on environment configuration.

    Tries providers in order: groq → openai → ollama.
    Falls back automatically if a provider's key is missing or fails.

    Args:
        temperature: LLM sampling temperature.
        streaming: Whether to enable streaming token output.

    Returns:
        A LangChain LLM instance ready for use.

    Raises:
        RuntimeError: If no LLM provider could be initialized.
    """
    preferred = os.getenv("LLM_PROVIDER", "groq").lower().strip()
    logger.info("llm_init_start", provider=preferred)

    # Build chain: preferred first, then remaining providers
    chain = [preferred] + [p for p in PROVIDER_CHAIN if p != preferred]

    last_error: Optional[Exception] = None
    for p in chain:
        try:
            llm = _build_llm(p, temperature, streaming)
            if llm is not None:
                if p != preferred:
                    logger.warning(
                        "llm_provider_fallback",
                        primary=preferred,
                        using=p,
                    )
                else:
                    logger.info("llm_init_success", provider=p)
                return llm
        except Exception as exc:
            logger.warning(
                "llm_init_failed",
                provider=p,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            last_error = exc

    raise RuntimeError(
        f"All LLM providers failed. "
        f"Please set GROQ_API_KEY (free at https://console.groq.com). "
        f"Last error: {last_error}"
    )


def _build_llm(provider: str, temperature: float, streaming: bool) -> Optional[object]:
    """
    Attempt to instantiate the specified LLM provider.

    Returns the LLM instance, or None if key is missing.
    """
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            logger.info("groq_no_key", reason="GROQ_API_KEY not set or placeholder")
            return None

        try:
            from langchain_groq import ChatGroq
        except ImportError:
            logger.warning("langchain_groq_missing", reason="pip install langchain-groq")
            return None

        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=4096,
            streaming=streaming,
        )

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            logger.info("openai_no_key", reason="OPENAI_API_KEY not set or placeholder")
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


async def invoke_with_retry(
    llm: object,
    prompt: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> str:
    """
    Invoke the LLM with retry logic and exponential backoff.

    Args:
        llm: A LangChain LLM instance.
        prompt: The text prompt to send.
        max_retries: Number of retry attempts.
        base_delay: Initial delay in seconds (doubles each retry).

    Returns:
        The LLM's text response.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("llm_invoke_attempt", attempt=attempt, prompt_length=len(prompt))
            response = await llm.ainvoke(prompt)
            content = getattr(response, "content", str(response))
            return content

        except Exception as exc:
            last_error = exc
            error_type = type(exc).__name__
            error_msg = str(exc)

            logger.warning(
                "llm_invoke_failed",
                attempt=attempt,
                max_retries=max_retries,
                error_type=error_type,
                error=error_msg[:200],
            )

            print(f"\n[LLM ERROR] Attempt {attempt}/{max_retries}: {error_type}: {error_msg}\n")

            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info("llm_retry_waiting", delay_seconds=delay)
                await asyncio.sleep(delay)

    # If all retries failed due to rate limiting, try Ollama as fallback
    if last_error and "429" in str(last_error):
        logger.warning("llm_rate_limited_trying_ollama", error=str(last_error)[:100])
        print("\n[FALLBACK] Groq rate limited — switching to local Ollama...\n")
        try:
            ollama_llm = _build_llm("ollama", temperature=0.3, streaming=False)
            if ollama_llm is not None:
                response = await ollama_llm.ainvoke(prompt)
                content = getattr(response, "content", str(response))
                logger.info("ollama_fallback_success", response_length=len(content))
                return content
        except Exception as ollama_exc:
            logger.warning("ollama_fallback_failed", error=str(ollama_exc)[:200])
            print(f"\n[FALLBACK FAILED] Ollama error: {ollama_exc}\n")

    raise RuntimeError(
        f"LLM call failed after {max_retries} attempts. "
        f"Last error ({type(last_error).__name__}): {str(last_error)}"
    )


async def test_llm_connection() -> dict:
    """
    Test the LLM connection by sending a minimal prompt.
    Tests Groq, then OpenAI, then Ollama — no Gemini.

    Returns:
        Dict with status, provider, model, and any error info.
    """
    try:
        llm = get_llm(temperature=0.0, streaming=False)

        # Determine which provider was initialised
        preferred = os.getenv("LLM_PROVIDER", "groq").lower().strip()

        start_time = time.time()
        response = await llm.ainvoke("Reply with exactly: CONNECTION_OK")
        content = getattr(response, "content", str(response))
        elapsed = round(time.time() - start_time, 2)

        return {
            "status": "ok",
            "provider": preferred,
            "model": _get_model_name(preferred),
            "response": content[:100],
            "latency_seconds": elapsed,
        }

    except Exception as exc:
        provider = os.getenv("LLM_PROVIDER", "groq")
        return {
            "status": "error",
            "provider": provider,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }


def _get_model_name(provider: str) -> str:
    """Get the model name for the given provider from env vars."""
    models = {
        "groq": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "ollama": os.getenv("OLLAMA_MODEL", "llama3"),
    }
    return models.get(provider, "unknown")


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
