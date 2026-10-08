from app.utils.insights import TOP_WORDS_LIMIT, compute_insights


def test_counts_characters_with_and_without_whitespace() -> None:
    insights = compute_insights("ab c\n d")
    assert insights.char_count == 7
    assert insights.char_count_no_whitespace == 4


def test_counts_words_case_insensitively_for_uniqueness() -> None:
    insights = compute_insights("Hello hello HELLO world")
    assert insights.word_count == 4
    assert insights.unique_word_count == 2


def test_runs_of_punctuation_end_one_sentence() -> None:
    assert compute_insights("One!!! Two?? Three...").sentence_count == 3


def test_paragraphs_are_split_on_blank_lines() -> None:
    assert compute_insights("First.\n\nSecond.\n  \nThird").paragraph_count == 3


def test_average_word_length_is_rounded() -> None:
    assert compute_insights("a bb ccc dddd").average_word_length == 2.5
    assert compute_insights("ab abc").average_word_length == 2.5
    assert compute_insights("a ab ab").average_word_length == 1.67


def test_top_words_skip_stopwords_and_are_capped() -> None:
    fillers = " ".join(f"word{letter}" for letter in "abcdefghijklmnopqrst")
    text = f"the cat and the dog cat dog cat {fillers}"
    top_words = compute_insights(text).top_words
    assert "the" not in top_words
    assert "and" not in top_words
    assert top_words[:2] == ["cat", "dog"]
    assert len(top_words) == TOP_WORDS_LIMIT


def test_reading_time_is_at_200_words_per_minute() -> None:
    assert compute_insights("word " * 200).estimated_reading_time_seconds == 60.0
    assert compute_insights("word " * 50).estimated_reading_time_seconds == 15.0


def test_empty_text_is_all_zeros_not_a_crash() -> None:
    insights = compute_insights("")
    assert insights.word_count == 0
    assert insights.average_word_length == 0.0
    assert insights.top_words == []
    assert insights.estimated_reading_time_seconds == 0.0
