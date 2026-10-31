"""
RAG Pipeline service.
Combines hybrid retrieval (graph nodes + raw chunks) and LLM generation
for the study chatbot.

Auto-detects "detail" intent in the question and switches to a comprehensive
mode that retrieves more context and instructs the LLM to cover everything.

Token budget management:
  - Context is hard-capped before being sent to the LLM to prevent TPM errors.
  - Normal mode:  max context ~3,000 chars  (~750 tokens) + 700 output = ~1,450 total
  - Detail mode:  max context ~6,000 chars  (~1,500 tokens) + 1,800 output = ~3,300 total
  Both stay safely under Groq free-tier limits (12,000 TPM for llama-3.3-70b).
"""

import logging
from app.services.llm_groq import generate
from app.utils.prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT,
    RAG_SYSTEM_PROMPT_DETAILED,
    RAG_USER_PROMPT_DETAILED,
)
from app.services.graph_service import get_hybrid_retriever
from app.services.graph_rag.engine import HybridRetrieverNotReadyError

logger = logging.getLogger(__name__)

# ── Token-budget constants ──────────────────────────────────────────
# Approx: 1 token ≈ 4 chars of English text
NORMAL_CONTEXT_CHAR_LIMIT  = 2_500   # ~625 tokens
DETAIL_CONTEXT_CHAR_LIMIT  = 5_000   # ~1,250 tokens
NORMAL_MAX_OUTPUT_TOKENS   = 600
DETAIL_MAX_OUTPUT_TOKENS   = 1_500

# ── Detail-intent keywords ──────────────────────────────────────────
_DETAIL_KEYWORDS = {
    "detail", "detailed", "in detail", "explain in detail", "full", "fully",
    "elaborate", "elaborate on", "everything", "all about", "complete",
    "comprehensive", "thorough", "deeply", "deep dive", "explain completely",
    "tell me everything", "explain fully", "more detail", "more details",
    "explain more", "more information", "all the points", "all points",
    "do not skip", "don't skip", "cover all", "in depth", "in-depth",
    "explain all", "complete explanation", "full explanation",
}


def _is_detail_request(question: str) -> bool:
    """Return True if the question is asking for a full/detailed explanation."""
    q_lower = question.lower()
    for phrase in sorted(_DETAIL_KEYWORDS, key=len, reverse=True):
        if phrase in q_lower:
            return True
    return False


def _trim_context(context: str, char_limit: int) -> str:
    """
    Trim context to char_limit while preserving whole sections.

    Tries to cut at a section boundary ("---") so we don't split mid-sentence.
    Falls back to hard truncation with a notice appended.
    """
    if len(context) <= char_limit:
        return context

    # Try to cut at the last section separator before the limit
    truncated = context[:char_limit]
    last_sep = truncated.rfind("\n\n---\n\n")
    if last_sep > char_limit * 0.5:  # Only use separator if we keep >50% of target
        return context[:last_sep] + "\n\n[... additional notes available — ask a more specific question to see them ...]"

    # Hard cut at last newline
    last_nl = truncated.rfind("\n")
    if last_nl > 0:
        return context[:last_nl] + "\n\n[... notes trimmed to fit — ask a more specific question for more ...]"

    return truncated + "\n\n[... notes trimmed ...]"


def ask(
    question: str,
    top_k: int = 5,
    hops: int = 2,
) -> dict:
    """
    Hybrid RAG pipeline: retrieve context → trim to token budget → generate answer.

    Detail mode is triggered automatically by keywords like "in detail",
    "explain fully", "everything about", etc.

    Args:
        question: The student's natural-language question.
        top_k: Number of seed nodes / raw chunks per collection (normal mode).
        hops: Graph traversal hops from each seed node.

    Returns:
        Dict with 'answer', 'sources', 'context_found', 'detail_mode'.
    """
    detail_mode = _is_detail_request(question)

    # Slightly more retrieval for detail mode, but still bounded
    effective_top_k = 6 if detail_mode else top_k
    effective_hops  = 2   # Keep hops at 2 to avoid runaway context explosion

    retriever = get_hybrid_retriever()

    try:
        context_string, entity_names = retriever.retrieve(
            question=question,
            top_k=effective_top_k,
            hops=effective_hops,
        )
    except HybridRetrieverNotReadyError:
        return {
            "answer": (
                "No study material has been uploaded yet. "
                "Please upload a PDF first, then I can help you!"
            ),
            "sources": [],
            "context_found": False,
            "detail_mode": detail_mode,
        }
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return {
            "answer": "Something went wrong while searching your notes. Please try again.",
            "sources": [],
            "context_found": False,
            "detail_mode": detail_mode,
        }

    if not context_string or not context_string.strip():
        return {
            "answer": "I could not find this in your notes. Try asking your teacher.",
            "sources": [],
            "context_found": False,
            "detail_mode": detail_mode,
        }

    # ── Trim context to token budget ────────────────────────────────
    char_limit = DETAIL_CONTEXT_CHAR_LIMIT if detail_mode else NORMAL_CONTEXT_CHAR_LIMIT
    context_string = _trim_context(context_string, char_limit)
    logger.info(
        f"Context size after trim: {len(context_string)} chars "
        f"({'detail' if detail_mode else 'normal'} mode)"
    )

    # ── Select prompt and generation settings ───────────────────────
    if detail_mode:
        system_prompt = RAG_SYSTEM_PROMPT_DETAILED
        user_prompt   = RAG_USER_PROMPT_DETAILED.format(
            context=context_string,
            question=question,
        )
        max_tokens  = DETAIL_MAX_OUTPUT_TOKENS
        temperature = 0.2
        logger.info(f"Detail mode: {question[:60]}")
    else:
        system_prompt = RAG_SYSTEM_PROMPT
        user_prompt   = RAG_USER_PROMPT.format(
            context=context_string,
            question=question,
        )
        max_tokens  = NORMAL_MAX_OUTPUT_TOKENS
        temperature = 0.3

    # ── Generate answer ─────────────────────────────────────────────
    answer = generate(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    sources = [{"source": entity, "chunk_index": 0} for entity in entity_names]

    return {
        "answer": answer,
        "sources": sources,
        "context_found": True,
        "detail_mode": detail_mode,
    }
