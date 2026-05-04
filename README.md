# FacultyTime

A desktop app that suggests the best office-hour time slots for faculty, based on when students are free.

## How to Run It

1. navigate to the google drive and install the zip file: https://drive.google.com/drive/folders/1Fb26HV6eYUKyoSW334qX99uQ-sPA2lR5?usp=sharing
2. run the 'facultytime.exe'


## How to Use the App

### Step 1 — Load your student schedule file

Click **Open CSV** and select a CSV file containing your students' busy times (when they are in class).

The CSV must have these four columns:

| Column    | What it means                              | Example      |
|-----------|--------------------------------------------|--------------|
| `student` | Student name or ID                         | `jsmith`     |
| `weekday` | Day of the week                            | `Monday`     |
| `start`   | When the busy block starts (24-hour time)  | `09:00`      |
| `end`     | When the busy block ends (24-hour time)    | `10:15`      |

See the `examples/` folder for a sample file.

### Step 2 — Set your preferences

| Setting      | What it controls                                        | Default   |
|--------------|---------------------------------------------------------|-----------|
| Slot length  | How long each office-hour block should be               | 60 min    |
| Search step  | How finely to scan for slots                            | 30 min    |
| Day window   | The earliest and latest time to consider               | 09:00–17:00 |
| Show top     | How many results to display                             | 25        |

### Step 3 — Click "Suggest office hours"

The app will rank every possible time slot by how many students are free for the full block. The slot where the most students are available appears at the top.

This is a **suggestion tool** — you choose what works best for you.

---

## For Developers

To run from source:

```
pip install -e ".[dev]"
python -m facultytime
```

To run tests:

```
pytest
```

To build the Windows executable:

```
pip install pyinstaller
python build_windows.py
```

---

## License

MIT