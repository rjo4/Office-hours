import pytest

from facultytime.csv_io import load_busy_csv


def test_load_busy_csv_merges_same_student_day() -> None:
    text = """student,weekday,start,end
s1,Monday,10:00,11:00
s1,Monday,10:30,11:30
"""
    s = load_busy_csv(text=text)
    assert "s1" in s
    assert s["s1"][0] == [(10 * 60, 11 * 60 + 30)]


def test_load_busy_csv_requires_columns() -> None:
    with pytest.raises(ValueError):
        load_busy_csv(text="a,b\n1,2\n")
