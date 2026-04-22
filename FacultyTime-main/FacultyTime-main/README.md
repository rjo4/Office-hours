# FacultyTime

Desktop helper for faculty to **suggest office-hour time windows** that fit the most students, using each student’s **busy** (in-class) blocks from a CSV. The graphical interface uses **Tkinter only** (Python standard library).

## What it does

1. You load a CSV where each row is one busy interval: which student, which weekday, start time, end time.
2. You choose how long each office-hour block should be (for example 60 minutes), how finely to step the search (for example every 30 minutes), and the daily time window (for example 09:00–17:00).
3. The app lists the **top candidate slots** ranked by how many students are **free** for the entire block (not in class).

This is a **suggestion** tool: you still pick what works for you.

## Requirements

- Python **3.10+** (includes Tkinter on most official Windows/macOS installers; on some Linux distributions install the `python3-tk` package).

## Run from source (developers)

From this folder:

```text
pip install -e ".[dev]"
python -m facultytime
```

Or, without installing the package:

```text
pip install pytest
set PYTHONPATH=src
python -m facultytime
```

(On PowerShell, use `$env:PYTHONPATH = "src"` instead of `set`.)

## Tests

```text
pip install -e ".[dev]"
pytest
```

## CSV format

UTF-8 file with a header row:

| Column   | Meaning                                      |
|----------|----------------------------------------------|
| `student`| Student id or name (string)                  |
| `weekday`| `Monday`–`Friday` or short forms like `Mon`  |
| `start`  | Busy start, 24-hour `HH:MM`                  |
| `end`    | Busy end, 24-hour `HH:MM`                    |

Example: `examples/sample_busy.csv`.

## End users (no command line)

For the course requirement of a desktop app that does not rely on end users using a terminal, **bundle** the app (for example with [PyInstaller](https://pyinstaller.org/)) into a single-folder or one-file executable. Build instructions are environment-specific; after bundling, users double-click the executable.

## License

MIT (see `pyproject.toml`).
