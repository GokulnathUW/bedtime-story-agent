"""Deterministic story metrics for eval (no LLM)."""

from __future__ import annotations

import textstat


def story_word_count(text: str) -> int:
    """Count words in story prose (whitespace-separated tokens)."""
    if not text or not text.strip():
        return 0
    return len(text.split())


def story_flesch_kincaid_grade(text: str) -> float:
    """Flesch-Kincaid grade level via textstat"""
    if not text or not text.strip():
        return 0.0
    return float(textstat.flesch_kincaid_grade(text))
