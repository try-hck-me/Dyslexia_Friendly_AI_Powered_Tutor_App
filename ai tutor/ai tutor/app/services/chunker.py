"""
Text chunking service.
Splits long text into overlapping chunks for embedding and retrieval.
Includes a section-aware chunker that respects chapter/section headings.
"""

import re


# ─────────────────────────────────────────────
# Section-Aware Chunker (primary for uploads)
# ─────────────────────────────────────────────

# Patterns that indicate a new section/chapter heading
_HEADING_PATTERNS = [
    re.compile(r'^\s*(?:chapter|unit|module)\s+\d+[\s:\-–—]', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*\d+\.\d+(?:\.\d+)?\s+[A-Za-z]', re.MULTILINE),  # 1.2 Some Title
    re.compile(r'^\s*\d+\s+[A-Z][A-Za-z\s]{5,}$', re.MULTILINE),    # 3 SOME TITLE
    re.compile(r'^[A-Z][A-Z\s\-]{10,}$', re.MULTILINE),              # ALL CAPS HEADING
    re.compile(r'^\s*(?:section|part|topic)\s+\d+', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(?:introduction|conclusion|summary|overview|background)\s*$', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^\s*(?:Q\.|Question\s*\d+|Exercise\s*\d+)', re.IGNORECASE | re.MULTILINE),
]


def _is_heading(line: str) -> bool:
    """Return True if the line looks like a chapter/section heading."""
    line = line.strip()
    if not line or len(line) > 120:
        return False
    for pattern in _HEADING_PATTERNS:
        if pattern.search(line):
            return True
    return False


def chunk_by_sections(
    text: str,
    source: str = "unknown",
    max_words_per_chunk: int = 600,
    overlap_words: int = 80,
) -> list[dict]:
    """
    Split text into section-aware chunks.

    Strategy:
    1. Split text at heading lines to create "sections".
    2. If a section is larger than max_words_per_chunk, further split it
       with word-based overlap chunking.
    3. Each chunk dict has: text, source, chunk_index, has_heading, heading.

    Returns:
        List of dicts with 'text', 'source', 'chunk_index', 'heading'.
    """
    lines = text.split('\n')
    sections: list[tuple[str, list[str]]] = []  # (heading, content_lines)

    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in lines:
        if _is_heading(line) and len(current_lines) > 2:
            # Save the current section
            sections.append((current_heading, current_lines))
            current_heading = line.strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Save final section
    if current_lines:
        sections.append((current_heading, current_lines))

    # If no headings were found, fall back to word-based chunking
    if len(sections) <= 1:
        return chunk_text_with_metadata(text, source=source, chunk_size=max_words_per_chunk, overlap=overlap_words)

    # Build final chunk list
    chunks: list[dict] = []
    chunk_index = 0

    for heading, content_lines in sections:
        section_text = '\n'.join(content_lines).strip()
        if not section_text:
            continue

        words = section_text.split()
        if len(words) <= max_words_per_chunk:
            # Section fits in one chunk
            chunks.append({
                "text": section_text,
                "source": source,
                "chunk_index": chunk_index,
                "heading": heading,
            })
            chunk_index += 1
        else:
            # Section is too large — split with overlap
            sub_chunks = _word_split(section_text, max_words_per_chunk, overlap_words)
            for i, sub in enumerate(sub_chunks):
                chunks.append({
                    "text": sub,
                    "source": source,
                    "chunk_index": chunk_index,
                    "heading": heading + f" (part {i + 1})",
                })
                chunk_index += 1

    return chunks


# ─────────────────────────────────────────────
# Word-based splitter (internal helper)
# ─────────────────────────────────────────────

def _word_split(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Split text into word-based chunks with overlap."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
        start += step

    return chunks


# ─────────────────────────────────────────────
# Legacy word-based API (used by quiz retriever)
# ─────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[str]:
    """
    Split text into word-based chunks with overlap.

    Args:
        text: The full text to chunk.
        chunk_size: Target number of words per chunk.
        overlap: Number of overlapping words between chunks.

    Returns:
        List of text chunks.
    """
    return _word_split(text, chunk_size, overlap)


def chunk_text_with_metadata(
    text: str,
    source: str = "unknown",
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[dict]:
    """
    Split text into chunks and attach metadata.

    Returns:
        List of dicts with 'text', 'source', 'chunk_index' keys.
    """
    chunks = chunk_text(text, chunk_size, overlap)
    return [
        {
            "text": chunk,
            "source": source,
            "chunk_index": i,
            "heading": "",
        }
        for i, chunk in enumerate(chunks)
    ]
