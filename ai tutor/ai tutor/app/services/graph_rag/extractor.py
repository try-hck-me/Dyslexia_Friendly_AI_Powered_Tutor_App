"""
Graph Extractor — LLM-based Knowledge Graph extraction from text chunks.

Uses the centralized GRAPH_EXTRACTION_SYSTEM_PROMPT from prompts.py.
Preserves original chunk text on every concept node for lossless retrieval.
"""

import json
import logging
import re
import time
from typing import Optional, Callable

from app.services.llm_groq import generate
from app.utils.prompts import GRAPH_EXTRACTION_SYSTEM_PROMPT, GRAPH_CHUNK_USER_PROMPT

logger = logging.getLogger(__name__)


def format_chunk_prompt(chunk: dict, chunk_index: int, total_chunks: int) -> str:
    """Build the user prompt for a single chunk."""
    return GRAPH_CHUNK_USER_PROMPT.format(
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        source=chunk.get("source", "unknown"),
        text=chunk.get("text", ""),
    )


def _extract_json(text: str) -> Optional[dict]:
    """Try multiple strategies to extract valid JSON from LLM output."""
    if not text:
        return None
    text = text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the outermost { ... } block
    brace_start = text.find("{")
    if brace_start == -1:
        return None
    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[brace_start:i + 1])
                except json.JSONDecodeError:
                    break
    return None


def generate_with_retries(
    user_prompt: str,
    expect_json: bool = True,
    max_retries: int = 2,
) -> dict | str:
    """Call the LLM with automatic retry on JSON parse failure."""
    last_error = None
    current_prompt = user_prompt

    for attempt in range(1, max_retries + 1):
        try:
            content = generate(
                user_prompt=current_prompt,
                system_prompt=GRAPH_EXTRACTION_SYSTEM_PROMPT,
                temperature=0.0,
                model="llama-3.1-8b-instant",
                max_tokens=4096,
            )
            if not expect_json:
                return content

            result = _extract_json(content)
            if result is not None:
                return result

            logger.warning(f"Attempt {attempt}: Could not parse JSON from LLM response.")
            last_error = "Invalid JSON in response"
            current_prompt = (
                current_prompt
                + "\n\nYour previous response was not valid JSON. "
                "Return ONLY a valid JSON object with no markdown, no extra text."
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(5 * attempt)

    raise RuntimeError(
        f"LLM generation failed after {max_retries} attempts. Last error: {last_error}"
    )


def _make_empty_result() -> dict:
    """Return an empty but valid extraction result."""
    return {
        "document_metadata": {"title": "", "subject": "", "processing_notes": "No content extracted"},
        "chapters": [],
        "relationships": [],
        "skipped_items": [],
    }


class Extractor:
    """
    Extracts a knowledge graph from a list of text chunks.

    Each extracted concept node carries the original raw chunk text
    in its `chunk_text` field so the retriever can serve exact content.
    """

    def __init__(self, progress_callback: Optional[Callable[[int, int, str], None]] = None):
        self.progress_callback = progress_callback
        self.results: list[dict] = []
        self.errors: list[dict] = []

    def _notify(self, current: int, total: int, message: str):
        if self.progress_callback:
            self.progress_callback(current, total, message)

    def extract_chunk(self, chunk: dict, index: int, total: int) -> dict:
        """Extract knowledge graph from a single chunk."""
        user_prompt = format_chunk_prompt(chunk, index, total)
        try:
            result = generate_with_retries(user_prompt, expect_json=True)
            if not isinstance(result, dict):
                raise ValueError(f"Expected dict, got {type(result)}")

            # Ensure required keys exist
            result.setdefault("document_metadata", {})
            result.setdefault("chapters", [])
            result.setdefault("relationships", [])
            result.setdefault("skipped_items", [])

            # Attach raw chunk text so it propagates into every concept node
            result["chunk_text"] = chunk.get("text", "")
            result["chunk_heading"] = chunk.get("heading", "")
            return result

        except Exception as e:
            logger.error(f"Extraction failed for chunk {index}: {e}")
            self.errors.append({"chunk_index": index, "error": str(e)})
            empty = _make_empty_result()
            empty["chunk_text"] = chunk.get("text", "")
            return empty

    def extract_all(self, chunks: list[dict], show_progress: bool = True) -> list[dict]:
        """Extract knowledge graphs from all chunks."""
        self.results.clear()
        self.errors.clear()
        total = len(chunks)
        logger.info(f"Starting extraction of {total} chunks")

        try:
            from tqdm import tqdm
            iterable = (
                tqdm(enumerate(chunks, 1), total=total, desc="Extracting knowledge", unit="chunk")
                if show_progress else enumerate(chunks, 1)
            )
        except ImportError:
            iterable = enumerate(chunks, 1)

        for idx, chunk in iterable:
            self._notify(idx, total, f"Processing chunk {idx}/{total}")
            result = self.extract_chunk(chunk, idx, total)
            self.results.append(result)
            time.sleep(1)  # Respect Groq rate limits

        success_count = total - len(self.errors)
        logger.info(
            f"Extraction complete: {success_count}/{total} chunks succeeded, "
            f"{len(self.errors)} errors"
        )
        return self.results
