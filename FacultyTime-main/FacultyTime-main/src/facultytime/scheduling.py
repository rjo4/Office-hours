"""Pure scheduling logic (no GUI) — easy to unit test."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

# Monday=0 .. Friday=4
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
_WEEKDAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
}


def parse_weekday(token: str) -> int:
    t = token.strip().lower()
    if t in _WEEKDAY_ALIASES:
        return _WEEKDAY_ALIASES[t]
    raise ValueError(f"Unknown weekday: {token!r}")


def parse_hhmm(token: str) -> int:
    s = token.strip()
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError(f"Expected HH:MM, got {token!r}")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Invalid time: {token!r}")
    return h * 60 + m


def merge_intervals(intervals: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    iv = sorted(intervals, key=lambda x: (x[0], x[1]))
    if not iv:
        return []
    out: list[tuple[int, int]] = [iv[0]]
    for s, e in iv[1:]:
        ls, le = out[-1]
        if s <= le:
            out[-1] = (ls, max(le, e))
        else:
            out.append((s, e))
    return out


def intervals_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Half-open [start, end) style: overlap if ranges intersect with positive length."""
    as_, ae = a
    bs, be = b
    return as_ < be and bs < ae


def student_free_for_slot(
    busy_on_day: list[tuple[int, int]], slot: tuple[int, int]
) -> bool:
    for b in busy_on_day:
        if intervals_overlap(b, slot):
            return False
    return True


def coverage_count(
    schedules: Mapping[str, dict[int, list[tuple[int, int]]]],
    weekday: int,
    slot: tuple[int, int],
) -> int:
    n = 0
    for _sid, days in schedules.items():
        busy = days.get(weekday, [])
        if student_free_for_slot(busy, slot):
            n += 1
    return n


@dataclass(frozen=True)
class RankedSlot:
    coverage: int
    weekday: int
    start_min: int
    end_min: int


def enumerate_slots(
    weekdays: tuple[int, ...],
    day_start_min: int,
    day_end_min: int,
    slot_duration_min: int,
    step_min: int,
) -> list[tuple[int, tuple[int, int]]]:
    """Yield (weekday, (start, end)) for each candidate window within [day_start, day_end)."""
    if slot_duration_min <= 0 or step_min <= 0:
        raise ValueError("slot_duration_min and step_min must be positive")
    if day_start_min >= day_end_min:
        raise ValueError("day window is empty")
    out: list[tuple[int, tuple[int, int]]] = []
    last_start = day_end_min - slot_duration_min
    for wd in weekdays:
        for start in range(day_start_min, last_start + 1, step_min):
            end = start + slot_duration_min
            out.append((wd, (start, end)))
    return out


def rank_office_hour_slots(
    schedules: Mapping[str, dict[int, list[tuple[int, int]]]],
    *,
    weekdays: tuple[int, ...] = (0, 1, 2, 3, 4),
    day_start_min: int = 9 * 60,
    day_end_min: int = 17 * 60,
    slot_duration_min: int = 60,
    step_min: int = 30,
    top_n: int = 25,
) -> list[RankedSlot]:
    candidates = enumerate_slots(
        weekdays, day_start_min, day_end_min, slot_duration_min, step_min
    )
    ranked: list[RankedSlot] = []
    for wd, slot in candidates:
        cov = coverage_count(schedules, wd, slot)
        ranked.append(RankedSlot(cov, wd, slot[0], slot[1]))
    ranked.sort(key=lambda r: (-r.coverage, r.weekday, r.start_min))
    return ranked[:top_n]


def format_minutes(m: int) -> str:
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}"
