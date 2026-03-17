"""
Chatbot handler for interacting with a specific research report.
Uses LangChain memory to maintain session context and limits
answers strictly to the papers available.

Chat messages are persisted to SQLite so they survive server restarts
and are accessible from the History page.
"""

import asyncio
from typing import Dict, AsyncGenerator

from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage

from models.llm_setup import get_llm
from utils.logger import get_logger
from utils.db import save_chat_message, get_chat_messages

logger = get_logger(__name__)

# In-memory cache of chat sessions mapping query_id -> memory
# Populated lazily from DB on first access
_chat_memories: Dict[str, ConversationBufferMemory] = {}

CHAT_SYSTEM_PROMPT = """You are an AI research assistant with deep knowledge of the papers \
in the current research report. Answer questions based ONLY on the \
papers and findings in this report. 

When answering:
- Cite which paper supports your answer
- If the answer is not in the papers, say "This isn't covered \
  in the papers I analyzed. You might want to search for..."
- Keep answers concise but complete
- Use the same mode as the report (technical language for expert, accessible for beginner)

Report context:
{report_text}

Papers analyzed:
{papers_list}
"""


async def _load_memory_from_db(query_id: str) -> ConversationBufferMemory:
    """
    Create a ConversationBufferMemory and pre-populate it with messages
    from the database. Called when no in-memory session exists yet.
    """
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    # Load persisted messages and replay them into memory
    messages = await get_chat_messages(query_id)
    for i in range(0, len(messages) - 1, 2):
        user_msg = messages[i]
        ai_msg = messages[i + 1] if i + 1 < len(messages) else None
        if user_msg["role"] == "user" and ai_msg and ai_msg["role"] == "assistant":
            memory.save_context(
                {"input": user_msg["content"]},
                {"output": ai_msg["content"]},
            )
    logger.info("chat_memory_loaded_from_db", query_id=query_id, message_count=len(messages))
    return memory


async def get_chat_memory(query_id: str) -> ConversationBufferMemory:
    """Retrieve or create/restore memory for a specific query_id session."""
    if query_id not in _chat_memories:
        _chat_memories[query_id] = await _load_memory_from_db(query_id)
        logger.info("chat_memory_ready", query_id=query_id)
    return _chat_memories[query_id]


async def stream_chat_response(
    query_id: str,
    message: str,
    report_text: str,
    papers: list,
) -> AsyncGenerator[str, None]:
    """
    Stream the LLM response for a chat message back to the client.
    Maintains history using ConversationBufferMemory and persists to SQLite.
    """
    llm = get_llm(temperature=0.3, streaming=True)
    memory = await get_chat_memory(query_id)

    # Format papers list for context
    papers_list = "\n".join([f"- {p.get('title')} ({p.get('year')})" for p in papers])

    system_message = CHAT_SYSTEM_PROMPT.format(
        report_text=report_text[:15000],  # Keep prompt sizes reasonable
        papers_list=papers_list
    )

    # Load history
    history = memory.load_memory_variables({})["chat_history"]

    # Build prompt string (supports all LLMs natively)
    prompt_lines = [system_message, "\n--- Chat History ---"]
    for h in history:
        if isinstance(h, HumanMessage):
            prompt_lines.append(f"User: {h.content}")
        elif isinstance(h, AIMessage):
            prompt_lines.append(f"Assistant: {h.content}")

    prompt_lines.append(f"User: {message}")
    prompt_lines.append("Assistant:")

    prompt = "\n".join(prompt_lines)

    full_response = ""
    try:
        # Persist the user message immediately
        await save_chat_message(query_id, "user", message)

        async for chunk in llm.astream(prompt):
            text = chunk.content if hasattr(chunk, "content") else str(chunk)
            full_response += text
            yield text

        # Save AI response and update in-memory history
        await save_chat_message(query_id, "assistant", full_response)
        memory.save_context({"input": message}, {"output": full_response})

    except Exception as exc:
        logger.error("chat_error", error=str(exc), query_id=query_id)
        yield f"\n\nError: {str(exc)}"


def clear_chat_history(query_id: str) -> None:
    """Clear the in-memory chat history for a specific report session."""
    if query_id in _chat_memories:
        _chat_memories[query_id].clear()
        logger.info("chat_history_cleared", query_id=query_id)


def get_chat_history_list(query_id: str) -> list:
    """Return the serialized chat history list for the frontend (in-memory only)."""
    if query_id not in _chat_memories:
        return []

    history = _chat_memories[query_id].load_memory_variables({})["chat_history"]
    result = []
    for h in history:
        role = "user" if isinstance(h, HumanMessage) else "assistant"
        result.append({"role": role, "content": h.content})
    return result
