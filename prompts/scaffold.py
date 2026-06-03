from __future__ import annotations

import re

# [Beat 1] or [Beat 1: Alice and Bob play hide-and-seek] (line or inline)
_BEAT_MARKER = re.compile(
    r"\[Beat\s+\d+(?:\s*:\s*[^\]]*)?\]",
    re.IGNORECASE,
)
# [S1], [S2], ... anywhere in the text
_S_MARKER     = re.compile(r"\[S\d+\]", re.IGNORECASE)
_HAS_SCAFFOLD = re.compile(r"\[(?:Beat\s+\d+|S\d+)\]", re.IGNORECASE)
_BEAT_SPLIT   = re.compile(r"(?=\[Beat\s+\d+)", re.IGNORECASE)


def _sentences_from_s_tags(text: str) -> list[str]:
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
    chunk = _BEAT_MARKER.sub("", chunk, count=1).strip()
    if not chunk:
        return None

    sentences = _sentences_from_s_tags(chunk)
    if sentences:
        return " ".join(sentences)

    # Tags present but no prose extracted — skip empty beat
    if _S_MARKER.search(chunk):
        return None

    return chunk


def strip_story_scaffolds(text: str) -> str:
    text = text.strip()
    if not _HAS_SCAFFOLD.search(text):
        return text

    paragraphs: list[str] = []
    for chunk in _BEAT_SPLIT.split(text):
        paragraph = _chunk_to_paragraph(chunk)
        if paragraph:
            paragraphs.append(paragraph)

    if not paragraphs:
        # Model used [S] tags without [Beat] headers
        only_s = " ".join(_sentences_from_s_tags(text))
        return only_s if only_s else text

    return "\n\n".join(paragraphs)
