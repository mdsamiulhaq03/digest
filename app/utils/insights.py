"""Pure functions for computing text insights (no HTTP, no storage)."""

import re
from collections import Counter

_WORD_RE = re.compile(r"[A-Za-z']+")
_SENTENCE_RE = re.compile(r"[.!?]+")
_PARAGRAPH_RE = re.compile(r"\n\s*\n")

WORDS_PER_MINUTE = 200

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "by",
    "can",
    "did",
    "do",
    "does",
    "else",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "just",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "she",
    "so",
    "such",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "these",
    "they",
    "this",
    "those",
    "to",
    "too",
    "very",
    "was",
    "we",
    "were",
    "will",
    "with",
    "you",
    "your",
}


def compute_insights(text: str) -> dict:
    char_count = len(text)
    char_count_no_whitespace = len("".join(text.split()))

    words = _WORD_RE.findall(text)
    word_count = len(words)
    lowered_words = [w.lower() for w in words]
    unique_word_count = len(set(lowered_words))

    sentence_count = len([s for s in _SENTENCE_RE.split(text) if s.strip()])

    paragraphs = [p for p in _PARAGRAPH_RE.split(text) if p.strip()]
    paragraph_count = len(paragraphs)

    average_word_length = (
        round(sum(len(w) for w in words) / word_count, 2) if word_count else 0.0
    )

    meaningful_words = [w for w in lowered_words if w not in _STOPWORDS]
    top_words = [word for word, _ in Counter(meaningful_words).most_common(10)]

    estimated_reading_time_seconds = round((word_count / WORDS_PER_MINUTE) * 60, 2)

    return {
        "char_count": char_count,
        "char_count_no_whitespace": char_count_no_whitespace,
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "average_word_length": average_word_length,
        "top_words": top_words,
        "estimated_reading_time_seconds": estimated_reading_time_seconds,
    }
