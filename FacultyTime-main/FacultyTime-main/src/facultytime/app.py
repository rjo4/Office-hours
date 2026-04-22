"""Tkinter desktop UI (stdlib only)."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from facultytime.csv_io import load_busy_csv
from facultytime.scheduling import (
    WEEKDAY_NAMES,
    format_minutes,
    parse_hhmm,
    rank_office_hour_slots,
)


class FacultyTimeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FacultyTime — office hour suggestions")
        self.minsize(640, 480)
        self._csv_path: Path | None = None
        self._schedules: dict | None = None

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open student CSV…", command=self._open_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        self._path_var = tk.StringVar(value="No file loaded")
        ttk.Label(top, textvariable=self._path_var).pack(anchor=tk.W)

        opts = ttk.Frame(top)
        opts.pack(fill=tk.X, pady=(8, 0))

        ttk.Label(opts, text="Slot length (minutes):").grid(row=0, column=0, sticky=tk.W)
        self._duration = tk.StringVar(value="60")
        dur = ttk.Combobox(
            opts,
            textvariable=self._duration,
            values=("30", "45", "60", "90"),
            width=6,
            state="readonly",
        )
        dur.grid(row=0, column=1, padx=(4, 16))

        ttk.Label(opts, text="Search step (minutes):").grid(row=0, column=2, sticky=tk.W)
        self._step = tk.StringVar(value="30")
        step = ttk.Combobox(
            opts,
            textvariable=self._step,
            values=("15", "30", "60"),
            width=6,
            state="readonly",
        )
        step.grid(row=0, column=3, padx=(4, 16))

        ttk.Label(opts, text="Day window:").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        self._day_start = tk.StringVar(value="09:00")
        self._day_end = tk.StringVar(value="17:00")
        ttk.Entry(opts, textvariable=self._day_start, width=8).grid(
            row=1, column=1, pady=(6, 0)
        )
        ttk.Label(opts, text="–").grid(row=1, column=2, pady=(6, 0))
        ttk.Entry(opts, textvariable=self._day_end, width=8).grid(
            row=1, column=3, pady=(6, 0)
        )

        ttk.Label(opts, text="Show top:").grid(row=1, column=4, sticky=tk.W, padx=(16, 0), pady=(6, 0))
        self._top_n = tk.StringVar(value="25")
        ttk.Spinbox(opts, from_=5, to=100, textvariable=self._top_n, width=5).grid(
            row=1, column=5, pady=(6, 0)
        )

        btn_row = ttk.Frame(top)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="Suggest office hours", command=self._run_suggest).pack(
            side=tk.LEFT
        )

        table_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("rank", "coverage", "day", "start", "end")
        self._tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=18,
            selectmode=tk.BROWSE,
        )
        self._tree.heading("rank", text="#")
        self._tree.heading("coverage", text="Students free")
        self._tree.heading("day", text="Day")
        self._tree.heading("start", text="Start")
        self._tree.heading("end", text="End")
        self._tree.column("rank", width=40, anchor=tk.CENTER)
        self._tree.column("coverage", width=100, anchor=tk.CENTER)
        self._tree.column("day", width=100)
        self._tree.column("start", width=80, anchor=tk.CENTER)
        self._tree.column("end", width=80, anchor=tk.CENTER)
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._status = tk.StringVar(value="Load a CSV of student busy times.")
        ttk.Label(self, textvariable=self._status, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM
        )

    def _open_csv(self) -> None:
        p = filedialog.askopenfilename(
            title="Open student busy CSV",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")],
        )
        if not p:
            return
        path = Path(p)
        try:
            self._schedules = load_busy_csv(path)
            self._csv_path = path
            n = len(self._schedules)
            self._path_var.set(str(path))
            self._status.set(f"Loaded {n} student(s). Click Suggest office hours.")
        except (OSError, ValueError) as e:
            messagebox.showerror("Could not load CSV", str(e))
            self._schedules = None
            self._csv_path = None

    def _parse_window(self) -> tuple[int, int]:
        ds = parse_hhmm(self._day_start.get())
        de = parse_hhmm(self._day_end.get())
        if ds >= de:
            raise ValueError("Day window: start must be before end.")
        return ds, de

    def _run_suggest(self) -> None:
        if not self._schedules:
            messagebox.showinfo("No data", "Open a CSV file first.")
            return
        try:
            slot_len = int(self._duration.get())
            step = int(self._step.get())
            top_n = int(self._top_n.get())
            day_start, day_end = self._parse_window()
        except ValueError as e:
            messagebox.showerror("Invalid settings", str(e))
            return

        self._tree.delete(*self._tree.get_children())
        try:
            ranked = rank_office_hour_slots(
                self._schedules,
                day_start_min=day_start,
                day_end_min=day_end,
                slot_duration_min=slot_len,
                step_min=step,
                top_n=top_n,
            )
        except ValueError as e:
            messagebox.showerror("Could not rank slots", str(e))
            return

        total = len(self._schedules)
        for i, r in enumerate(ranked, start=1):
            day = WEEKDAY_NAMES[r.weekday]
            self._tree.insert(
                "",
                tk.END,
                values=(
                    i,
                    f"{r.coverage} / {total}",
                    day,
                    format_minutes(r.start_min),
                    format_minutes(r.end_min),
                ),
            )
        self._status.set(
            f"Top {len(ranked)} slot(s) by student coverage (of {total} students)."
        )


def run_app() -> None:
    app = FacultyTimeApp()
    app.mainloop()
