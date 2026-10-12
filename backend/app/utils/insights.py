"""Pure functions for computing text insights (no HTTP, no storage)."""

import re
from collections import Counter
from dataclasses import dataclass

_WORD_RE = re.compile(r"[A-Za-z']+")
_SENTENCE_RE = re.compile(r"[.!?]+")
_PARAGRAPH_RE = re.compile(r"\n\s*\n")

WORDS_PER_MINUTE = 200
SECONDS_PER_MINUTE = 60
TOP_WORDS_LIMIT = 10
DECIMAL_PLACES = 2

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


@dataclass(frozen=True)
class TextInsights:
    char_count: int
    char_count_no_whitespace: int
    word_count: int
    unique_word_count: int
    sentence_count: int
    paragraph_count: int
    average_word_length: float
    top_words: list[str]
    estimated_reading_time_seconds: float


def compute_insights(text: str) -> TextInsights:
    words = _WORD_RE.findall(text)
    lowered_words = [word.lower() for word in words]
    return TextInsights(
        char_count=len(text),
        char_count_no_whitespace=_count_non_whitespace(text),
        word_count=len(words),
        unique_word_count=len(set(lowered_words)),
        sentence_count=_count_non_blank(_SENTENCE_RE.split(text)),
        paragraph_count=_count_non_blank(_PARAGRAPH_RE.split(text)),
        average_word_length=_average_length(words),
        top_words=_top_words(lowered_words),
        estimated_reading_time_seconds=_reading_time_seconds(len(words)),
    )


def _count_non_whitespace(text: str) -> int:
    return len("".join(text.split()))


def _count_non_blank(chunks: list[str]) -> int:
    return sum(1 for chunk in chunks if chunk.strip())


def _average_length(words: list[str]) -> float:
    if not words:
        return 0.0
    return round(sum(len(word) for word in words) / len(words), DECIMAL_PLACES)


def _top_words(lowered_words: list[str]) -> list[str]:
    meaningful = [word for word in lowered_words if word not in _STOPWORDS]
    return [word for word, _ in Counter(meaningful).most_common(TOP_WORDS_LIMIT)]


def _reading_time_seconds(word_count: int) -> float:
    minutes = word_count / WORDS_PER_MINUTE
    return round(minutes * SECONDS_PER_MINUTE, DECIMAL_PLACES)
