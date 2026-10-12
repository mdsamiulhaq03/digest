"""Pure functions for computing CSV insights (no HTTP, no storage).

One pass over the rows, keeping a running summary per column, so memory stays
proportional to the number of columns rather than the size of the file.
"""

import csv
import io
import re
from dataclasses import dataclass

DECIMAL_PLACES = 2
_BOM = "﻿"

# Deliberately stricter than int()/float(), which also accept "1_000", "nan"
# and "inf" - none of which a person means as a number in a spreadsheet.
_INTEGER_RE = re.compile(r"[+-]?\d+")
_FLOAT_RE = re.compile(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?")
_BOOLEANS = {"true", "false"}


@dataclass(frozen=True)
class ColumnStats:
    name: str
    null_count: int
    inferred_type: str  # integer | float | boolean | string | empty
    min: float | None
    max: float | None
    mean: float | None


@dataclass(frozen=True)
class CsvInsights:
    row_count: int
    column_count: int
    columns: list[ColumnStats]


def compute_csv_insights(text: str) -> CsvInsights:
    rows = csv.reader(io.StringIO(text.removeprefix(_BOM)))
    header = next(rows, [])
    summaries = [_ColumnSummary(name.strip()) for name in header]

    row_count = 0
    for row in rows:
        if not row:  # a blank line, not a row of empty cells
            continue
        row_count += 1
        for index, summary in enumerate(summaries):
            summary.add(row[index] if index < len(row) else "")

    return CsvInsights(
        row_count=row_count,
        column_count=len(summaries),
        columns=[summary.to_stats() for summary in summaries],
    )


class _ColumnSummary:
    """Running totals for one column. Only ever touched inside one call to
    compute_csv_insights, so its mutation never escapes."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.null_count = 0
        self.value_count = 0
        self.could_be_integer = True
        self.could_be_float = True
        self.could_be_boolean = True
        self.total = 0.0
        self.smallest: float | None = None
        self.largest: float | None = None

    def add(self, raw: str) -> None:
        value = raw.strip()
        if not value:
            self.null_count += 1
            return
        self.value_count += 1
        self.could_be_integer = self.could_be_integer and bool(
            _INTEGER_RE.fullmatch(value)
        )
        self.could_be_boolean = self.could_be_boolean and value.lower() in _BOOLEANS
        if self.could_be_float and _FLOAT_RE.fullmatch(value):
            self._add_number(float(value))
        else:
            self.could_be_float = False

    def _add_number(self, number: float) -> None:
        self.total += number
        self.smallest = number if self.smallest is None else min(self.smallest, number)
        self.largest = number if self.largest is None else max(self.largest, number)

    def inferred_type(self) -> str:
        if self.value_count == 0:
            return "empty"
        if self.could_be_integer:
            return "integer"
        if self.could_be_float:
            return "float"
        if self.could_be_boolean:
            return "boolean"
        return "string"

    def to_stats(self) -> ColumnStats:
        inferred_type = self.inferred_type()
        if inferred_type not in ("integer", "float"):
            return ColumnStats(
                self.name, self.null_count, inferred_type, None, None, None
            )
        as_type = int if inferred_type == "integer" else float
        return ColumnStats(
            name=self.name,
            null_count=self.null_count,
            inferred_type=inferred_type,
            min=as_type(self.smallest),
            max=as_type(self.largest),
            mean=round(self.total / self.value_count, DECIMAL_PLACES),
        )
