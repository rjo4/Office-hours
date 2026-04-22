import pytest

from facultytime.scheduling import (
    coverage_count,
    merge_intervals,
    parse_hhmm,
    parse_weekday,
    rank_office_hour_slots,
    student_free_for_slot,
)


def test_parse_weekday() -> None:
    assert parse_weekday("Monday") == 0
    assert parse_weekday("fri") == 4


def test_parse_weekday_bad() -> None:
    with pytest.raises(ValueError):
        parse_weekday("Saturday")


def test_merge_intervals() -> None:
    assert merge_intervals([(10, 20), (15, 25)]) == [(10, 25)]
    assert merge_intervals([(30, 40), (10, 20)]) == [(10, 20), (30, 40)]


def test_coverage_count() -> None:
    schedules = {
        "a": {0: [(10 * 60, 11 * 60)]},
        "b": {0: []},
    }
    assert coverage_count(schedules, 0, (11 * 60, 12 * 60)) == 2


def test_rank_prefers_more_students() -> None:
    schedules = {
        "s1": {0: [(9 * 60, 15 * 60)]},
        "s2": {0: [(16 * 60, 17 * 60)]},
    }
    top = rank_office_hour_slots(
        schedules,
        day_start_min=9 * 60,
        day_end_min=17 * 60,
        slot_duration_min=60,
        step_min=60,
        top_n=10,
    )
    assert top[0].weekday == 0
    assert top[0].start_min == 15 * 60
    assert top[0].end_min == 16 * 60
    assert top[0].coverage == 2


def test_parse_hhmm() -> None:
    assert parse_hhmm("09:30") == 9 * 60 + 30


def test_student_free() -> None:
    assert student_free_for_slot([(100, 200)], (200, 300)) is True
    assert student_free_for_slot([(100, 200)], (150, 250)) is False
