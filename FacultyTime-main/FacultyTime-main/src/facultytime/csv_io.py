"""Load student busy blocks from a simple CSV."""

from __future__ import annotations

import csv
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import TextIO

from facultytime.scheduling import merge_intervals, parse_hhmm, parse_weekday


def load_busy_csv(
    path: str | Path | None = None,
    text: str | None = None,
    *,
    encoding: str = "utf-8-sig",
) -> dict[str, dict[int, list[tuple[int, int]]]]:
    """
    Build schedules: student_id -> weekday_index -> merged busy intervals (minutes).
    Provide either path or text.
    """
    if (path is None) == (text is None):
        raise ValueError("Provide exactly one of path or text")
    if path is not None:
        with open(path, encoding=encoding, newline="") as f:
            return _load_from_file(f)
    return _load_from_file(StringIO(text))


def _load_from_file(f: TextIO) -> dict[str, dict[int, list[tuple[int, int]]]]:
    raw = list(csv.DictReader(f))
    if not raw:
        return {}

    # Normalize keys (strip BOM/spaces)
    rows = []
    for row in raw:
        rows.append({k.strip().lstrip("\ufeff").lower(): (v or "").strip() for k, v in row.items()})

    acc: dict[str, dict[int, list[tuple[int, int]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row in rows:
        try:
            student = row["student"]
            wd = parse_weekday(row["weekday"])
            s = parse_hhmm(row["start"])
            e = parse_hhmm(row["end"])
        except KeyError as exc:
            raise ValueError(
                "Each row needs columns: student, weekday, start, end"
            ) from exc
        if not student:
            continue
        if s >= e:
            raise ValueError(f"start must be before end: {row}")
        acc[student][wd].append((s, e))

    merged: dict[str, dict[int, list[tuple[int, int]]]] = {}
    for student, days in acc.items():
        merged[student] = {
            d: merge_intervals(ivs) for d, ivs in days.items()
        }
    return merged
