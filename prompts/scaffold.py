"""Strip beat/sentence scaffolding from story_writer model output."""

from __future__ import annotations

import re

# [Beat 1] or [Beat 1: Alice and Bob play hide-and-seek] (line or inline)
_BEAT_MARKER = re.compile(
    r"\[Beat\s+\d+(?:\s*:\s*[^\]]*)?\]",
    re.IGNORECASE,
)
# [S1], [S2], ... anywhere in the text
_S_MARKER = re.compile(r"\[S\d+\]", re.IGNORECASE)
_HAS_SCAFFOLD = re.compile(r"\[(?:Beat\s+\d+|S\d+)\]", re.IGNORECASE)
# Split before each beat marker so one-line multi-beat output still parses
_BEAT_SPLIT = re.compile(r"(?=\[Beat\s+\d+)", re.IGNORECASE)


def _sentences_from_s_tags(text: str) -> list[str]:
    """Extract prose segments between [S1], [S2], ... (multiple per line OK)."""
    markers = list(_S_MARKER.finditer(text))
    if not markers:
        return []

    sentences: list[str] = []
    for i, m in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        prose = text[m.end() : end].strip()
        if prose:
            sentences.append(prose)
    return sentences


def _chunk_to_paragraph(chunk: str) -> str | None:
    """Turn one beat chunk into a paragraph string, or None if empty."""
    chunk = _BEAT_MARKER.sub("", chunk, count=1).strip()
    if not chunk:
        return None

    sentences = _sentences_from_s_tags(chunk)
    if sentences:
        return " ".join(sentences)

    if _S_MARKER.search(chunk):
        return None

    return chunk


def strip_story_scaffolds(text: str) -> str:
    """Turn scaffolded story_writer output into plain prose paragraphs.

    Removes [Beat N: ...] markers and [S1]..[Sn] tags (including several [Sn]
    on one line), groups each beat's sentences into one paragraph, and joins
    paragraphs with blank lines. If the text has no beat/sentence tags, returns
    it unchanged (aside from strip).
    """
    text = text.strip()
    if not text or not _HAS_SCAFFOLD.search(text):
        return text

    paragraphs: list[str] = []
    for chunk in _BEAT_SPLIT.split(text):
        paragraph = _chunk_to_paragraph(chunk)
        if paragraph:
            paragraphs.append(paragraph)

    if not paragraphs:
        # Only [S] tags, no [Beat] markers
        only_s = " ".join(_sentences_from_s_tags(text))
        return only_s if only_s else text

    return "\n\n".join(paragraphs)
