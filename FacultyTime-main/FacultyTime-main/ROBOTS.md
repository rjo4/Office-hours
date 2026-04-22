# ROBOTS — machine-oriented project map

Purpose: help AI agents and automation navigate this repository without guessing.

## Root

- `pyproject.toml` — package metadata, `facultytime` console script, optional `[dev]` extras (`pytest`), pytest config (`pythonpath = ["src"]`).
- `README.md` — human-facing setup and usage.
- `ROBOTS.md` — this file.
- `src/facultytime/` — installable Python package (use `src` layout).
- `tests/` — `pytest` tests; run from repo root with `pytest`.
- `examples/` — sample inputs (e.g. `sample_busy.csv`).
- `.github/workflows/test.yml` — CI: install editable package with `[dev]`, run `pytest`.

## Entry points

- **GUI:** `python -m facultytime` → `facultytime/__main__.py` → `facultytime.app.run_app()`.
- **Console script:** `facultytime` (same as above) after `pip install -e .`.

## Module responsibilities

| Module            | Role |
|-------------------|------|
| `scheduling.py`   | Pure functions: parse times/weekdays, merge intervals, score candidate slots, `rank_office_hour_slots`. **No I/O, no Tkinter.** |
| `csv_io.py`       | `load_busy_csv(path=…)` or `load_busy_csv(text=…)` → nested dict `student → weekday_index → [(start_min, end_min)]` with merged busy intervals. |
| `app.py`          | Tkinter UI only: file dialog, settings, results table. Calls `load_busy_csv` and `rank_office_hour_slots`. |

## Conventions

- Weekdays: `0 = Monday` … `4 = Friday` (`WEEKDAY_NAMES` in `scheduling.py`).
- Times: minutes from midnight for the **same day** (0–1440), half-open busy intervals for overlap checks consistent with `intervals_overlap`.
- Changing ranking rules: edit `scheduling.py` and add/adjust tests in `tests/test_scheduling.py`.
- Changing CSV columns: update `csv_io.py`, `app.py` (if UI copy), `README.md`, and `tests/test_csv_io.py`.

## Do not

- Add non-stdlib GUI dependencies without an explicit product decision (project targets Tkinter-only).
- Put business logic only inside `app.py` — keep it testable in `scheduling.py` / `csv_io.py`.
