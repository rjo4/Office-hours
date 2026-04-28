"""Tkinter desktop UI (stdlib only)."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import ctypes

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
        self.geometry("760x720")
        self.minsize(700, 620)
        self._csv_path: Path | None = None
        self._schedules: dict | None = None

        # --- UI MODERNIZATION ---
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        self._set_theme("light")  # Load light mode by default

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open student CSV…", command=self._open_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # Theme Menu (NEW)
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Light", command=lambda: self._set_theme("light"))
        theme_menu.add_command(label="Dark", command=lambda: self._set_theme("dark"))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        self.config(menu=menubar)

        top = ttk.Frame(self, style="App.TFrame", padding=(16, 14, 16, 8))
        top.pack(fill=tk.X)

        header = ttk.Frame(top, style="App.TFrame")
        header.pack(fill=tk.X)

        ttk.Label(
            header,
            text="FacultyTime",
            style="Title.TLabel"
        ).pack(side=tk.LEFT)

        ttk.Button(
            header,
            text="Open CSV…",
            command=self._open_csv
        ).pack(side=tk.RIGHT)

        self._path_var = tk.StringVar(value="No CSV loaded")
        ttk.Label(
            top,
            textvariable=self._path_var,
            style="Subtle.TLabel"
        ).pack(anchor=tk.W, pady=(4, 10))

        opts = ttk.LabelFrame(top, text="Search settings", padding=12)
        opts.pack(fill=tk.X)

        ttk.Label(opts, text="Slot length (minutes):").grid(row=0, column=0, sticky=tk.W)
        self._duration = tk.StringVar(value="60")
        dur = ttk.Combobox(
            opts,
            textvariable=self._duration,
            values=("30", "45", "60", "90"),
            width=6,
            state="readonly",
        )
        dur.grid(row=0, column=1, padx=(4, 16), sticky=tk.W)

        ttk.Label(opts, text="Search step (minutes):").grid(row=0, column=2, sticky=tk.W)
        self._step = tk.StringVar(value="30")
        step = ttk.Combobox(
            opts,
            textvariable=self._step,
            values=("15", "30", "60"),
            width=6,
            state="readonly",
        )
        step.grid(row=0, column=3, padx=(4, 16), sticky=tk.W)

        ttk.Label(opts, text="Day window:").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        self._day_start = tk.StringVar(value="09:00")
        self._day_end = tk.StringVar(value="17:00")
        ttk.Entry(opts, textvariable=self._day_start, width=8).grid(
            row=1, column=1, padx=(4, 16), pady=(6, 0), sticky=tk.W
        )
        ttk.Label(opts, text="–").grid(row=1, column=2, pady=(6, 0))
        ttk.Entry(opts, textvariable=self._day_end, width=8).grid(
            row=1, column=3, padx=(4, 16), pady=(6, 0), sticky=tk.W
        )
        ttk.Label(opts, text="Show top:").grid(row=1, column=4, sticky=tk.W, padx=(16, 0), pady=(6, 0))
        self._top_n = tk.StringVar(value="25")
        ttk.Spinbox(opts, from_=5, to=100, textvariable=self._top_n, width=5).grid(
            row=1, column=5, pady=(6, 0), sticky=tk.W
        )

        btn_row = ttk.Frame(top, style="App.TFrame")
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(
            btn_row,
            text="Suggest office hours",
            command=self._run_suggest,
            style="Primary.TButton"
        ).pack(side=tk.LEFT)

        table_frame = ttk.Frame(self, padding=(8, 8, 8, 8))
        table_frame.pack(fill=tk.X)

        cols = ("rank", "coverage", "day", "start", "end")
        self._tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=12,
            selectmode=tk.BROWSE,
        )
        self._tree.heading("rank", text="#")
        self._tree.heading("coverage", text="Students free")
        self._tree.heading("day", text="Day", anchor=tk.CENTER)
        self._tree.heading("start", text="Start")
        self._tree.heading("end", text="End")
        self._tree.column("rank", width=40, anchor=tk.CENTER)
        self._tree.column("coverage", width=100, anchor=tk.CENTER)
        self._tree.column("day", width=100, anchor=tk.CENTER)
        self._tree.column("start", width=80, anchor=tk.CENTER)
        self._tree.column("end", width=80, anchor=tk.CENTER)
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._tree.tag_configure("oddrow", background="#ffffff")
        self._tree.tag_configure("evenrow", background="#f9fafb")
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._status = tk.StringVar(value="Load a CSV of student busy times.")
        ttk.Label(
            self,
            textvariable=self._status,
            style="Status.TLabel",
            anchor=tk.W,
        ).pack(fill=tk.X, side=tk.BOTTOM)

    def _set_theme(self, mode: str) -> None:
        style = ttk.Style(self)

        if mode == "dark":
            bg = "#1f2328"
            card_bg = "#2b3036"
            fg = "#f2f2f2"
            muted = "#b8c0cc"
            field_bg = "#363c44"
            tree_head = "#3c444f"
            row_odd = "#2b3036"
            row_even = "#252a30"
            select_bg = "#2563eb"
            button_bg = "#2563eb"
            button_active = "#1d4ed8"
        else:
            bg = "#f3f4f6"
            card_bg = "#ffffff"
            fg = "#111827"
            muted = "#6b7280"
            field_bg = "#ffffff"
            tree_head = "#e5e7eb"
            row_odd = "#ffffff"
            row_even = "#f9fafb"
            select_bg = "#2563eb"
            button_bg = "#2563eb"
            button_active = "#1d4ed8"

        self.configure(bg=bg)

        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            dark_title_bar = ctypes.c_int(1 if mode == "dark" else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                20,
                ctypes.byref(dark_title_bar),
                ctypes.sizeof(dark_title_bar),
            )
        except Exception:
            pass

        style.configure(".", background=bg, foreground=fg, font=("Segoe UI", 10))

        style.configure("App.TFrame", background=bg)
        style.configure("Card.TFrame", background=card_bg)

        style.configure(
            "Title.TLabel",
            background=bg,
            foreground=fg,
            font=("Segoe UI", 16, "bold"),
        )

        style.configure(
            "Subtle.TLabel",
            background=bg,
            foreground=muted,
            font=("Segoe UI", 9),
        )

        style.configure(
            "Status.TLabel",
            background=tree_head,
            foreground=fg,
            padding=(10, 4),
        )

        style.configure(
            "TLabelframe",
            background=bg,
            foreground=fg,
            padding=10,
        )

        style.configure(
            "TLabelframe.Label",
            background=bg,
            foreground=muted,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "TEntry",
            fieldbackground=field_bg,
            foreground=fg,
            padding=4,
        )

        style.configure(
            "TSpinbox",
            fieldbackground=field_bg,
            foreground=fg,
            padding=4,
        )

        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=field_bg,
            foreground=fg,
            padding=4,
        )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", field_bg)],
            foreground=[("readonly", fg)],
        )

        self.option_add("*TCombobox*Listbox.background", field_bg)
        self.option_add("*TCombobox*Listbox.foreground", fg)
        self.option_add("*TCombobox*Listbox.selectBackground", select_bg)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        style.configure(
            "Primary.TButton",
            background=button_bg,
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 7),
        )

        style.map(
            "Primary.TButton",
            background=[("active", button_active)],
            foreground=[("active", "#ffffff")],
        )

        style.configure(
            "TButton",
            padding=(10, 5),
        )

        style.configure(
            "Treeview",
            background=field_bg,
            fieldbackground=field_bg,
            foreground=fg,
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Treeview.Heading",
            background=tree_head,
            foreground=fg,
            font=("Segoe UI", 10, "bold"),
            padding=(8, 8),
        )

        style.map(
            "Treeview",
            background=[("selected", select_bg)],
            foreground=[("selected", "#ffffff")],
        )

        if hasattr(self, "_tree"):
            self._tree.tag_configure("oddrow", background=row_odd, foreground=fg)
            self._tree.tag_configure("evenrow", background=row_even, foreground=fg)

        self.update()

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
            self._path_var.set(f"Loaded: {path.name}")
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
            should_open = messagebox.askyesno(
                "No data",
                "No file loaded. Would you like to open a CSV file now?"
            )

            if should_open:
                self._open_csv()

            if not self._schedules:
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

            if i % 2 == 0:
                row_tag = "evenrow"
            else:
                row_tag = "oddrow"

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
                tags=(row_tag,),
            )

        self._status.set(
            f"Top {len(ranked)} slot(s) by student coverage (of {total} students)."
        )


def run_app() -> None:
    app = FacultyTimeApp()
    app.mainloop()
