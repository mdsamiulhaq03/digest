from app.utils.csv_insights import ColumnStats, compute_csv_insights


def _column(text: str, name: str) -> ColumnStats:
    columns = compute_csv_insights(text).columns
    return next(column for column in columns if column.name == name)


def test_counts_rows_and_columns_excluding_the_header() -> None:
    insights = compute_csv_insights("a,b,c\n1,2,3\n4,5,6\n")
    assert insights.row_count == 2
    assert insights.column_count == 3
    assert [column.name for column in insights.columns] == ["a", "b", "c"]


def test_empty_file_is_all_zeros_not_a_crash() -> None:
    insights = compute_csv_insights("")
    assert insights.row_count == 0
    assert insights.column_count == 0
    assert insights.columns == []


def test_header_only_gives_empty_columns() -> None:
    insights = compute_csv_insights("a,b\n")
    assert insights.row_count == 0
    assert [column.inferred_type for column in insights.columns] == ["empty", "empty"]


def test_header_names_lose_whitespace_and_the_bom() -> None:
    insights = compute_csv_insights("﻿ id , name \n1,x\n")
    assert [column.name for column in insights.columns] == ["id", "name"]


def test_blank_and_whitespace_cells_are_nulls_but_na_is_text() -> None:
    column = _column("v\n1\n\n  \nNA\n", "v")
    # The blank line is skipped entirely; "  " is a null; "NA" is a value.
    assert column.null_count == 1
    assert column.inferred_type == "string"


def test_short_rows_count_missing_cells_as_null() -> None:
    insights = compute_csv_insights("a,b,c\n1\n2,3\n")
    assert [column.null_count for column in insights.columns] == [0, 1, 2]


def test_cells_beyond_the_header_are_ignored() -> None:
    insights = compute_csv_insights("a,b\n1,2,3,4\n")
    assert insights.column_count == 2


def test_integer_column_stats() -> None:
    column = _column("n\n3\n-1\n+10\n", "n")
    assert column.inferred_type == "integer"
    assert (column.min, column.max, column.mean) == (-1, 10, 4.0)
    assert isinstance(column.min, int)


def test_integers_mixed_with_floats_are_float() -> None:
    column = _column("n\n1\n2.5\n1e1\n", "n")
    assert column.inferred_type == "float"
    assert (column.min, column.max, column.mean) == (1.0, 10.0, 4.5)


def test_mean_is_rounded() -> None:
    assert _column("n\n1\n1\n2\n", "n").mean == 1.33


def test_nulls_do_not_count_toward_the_mean() -> None:
    # Two columns: in a one-column file an empty cell is just a blank line.
    column = _column("n,label\n2,a\n,b\n4,c\n", "n")
    assert column.null_count == 1
    assert column.mean == 3.0


def test_boolean_column_has_no_numeric_stats() -> None:
    column = _column("flag\ntrue\nFALSE\nTrue\n", "flag")
    assert column.inferred_type == "boolean"
    assert (column.min, column.max, column.mean) == (None, None, None)


def test_one_text_value_makes_the_column_string() -> None:
    column = _column("n\n1\n2\nthree\n", "n")
    assert column.inferred_type == "string"
    assert column.mean is None


def test_python_number_spellings_are_not_numbers() -> None:
    # float() accepts all of these; a spreadsheet user never means them.
    for value in ("nan", "inf", "1_000"):
        assert _column(f"n\n{value}\n", "n").inferred_type == "string"


def test_all_null_column_is_empty() -> None:
    column = _column("a,b\n1,\n2,\n", "b")
    assert column.inferred_type == "empty"
    assert column.null_count == 2


def test_quoted_cells_with_commas_and_newlines() -> None:
    insights = compute_csv_insights('name,notes\nx,"a, b"\ny,"line1\nline2"\n')
    assert insights.row_count == 2
    assert _column('name,notes\nx,"a, b"\n', "notes").inferred_type == "string"
