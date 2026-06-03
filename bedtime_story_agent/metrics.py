import textstat


def story_word_count(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())


def story_flesch_kincaid_grade(text: str) -> float:
    if not text.strip():
        return 0.0
    return float(textstat.flesch_kincaid_grade(text))
