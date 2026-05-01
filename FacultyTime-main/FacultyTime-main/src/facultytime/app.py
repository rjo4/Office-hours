"""Tkinter desktop UI (stdlib only)."""

from __future__ import annotations

import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from facultytime.csv_io import load_busy_csv
from facultytime.scheduling import (
    WEEKDAY_NAMES,
    format_minutes,
    parse_hhmm,
    rank_office_hour_slots_decision_tree,
)


class FacultyTimeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FacultyTime")
        self.geometry("800x760")
        self.minsize(720, 640)
        self._theme_mode = "light"
        self._csv_path: Path | None = None
        self._schedules: dict | None = None

        style = ttk.Style(self)
        style.theme_use("clam")

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open student CSV…", command=self._open_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Light", command=lambda: self._set_theme("light"))
        theme_menu.add_command(label="Dark", command=lambda: self._set_theme("dark"))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        self.config(menu=menubar)

        main = ttk.Frame(self, style="App.TFrame")
        main.pack(fill=tk.BOTH, expand=True)

        head = ttk.Frame(main, style="App.TFrame", padding=(28, 24, 28, 12))
        head.pack(fill=tk.X)

        head_top = ttk.Frame(head, style="App.TFrame")
        head_top.pack(fill=tk.X)

        brand = ttk.Frame(head_top, style="App.TFrame")
        brand.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(brand, text="SCHEDULING", style="Eyebrow.TLabel").pack(anchor=tk.W)
        ttk.Label(brand, text="FacultyTime", style="Hero.TLabel").pack(anchor=tk.W, pady=(2, 0))
        ttk.Label(
            brand,
            text="Find office-hour windows where the most students are free.",
            style="Tagline.TLabel",
        ).pack(anchor=tk.W, pady=(6, 0))

        btn_head = ttk.Frame(head_top, style="App.TFrame")
        btn_head.pack(side=tk.RIGHT, anchor=tk.N, pady=(8, 0))
        ttk.Button(
            btn_head,
            text="Open CSV",
            command=self._open_csv,
            style="Ghost.TButton",
        ).pack(side=tk.RIGHT)

        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=28, pady=(0, 4))

        path_row = ttk.Frame(main, style="App.TFrame", padding=(28, 0, 28, 16))
        path_row.pack(fill=tk.X)
        self._path_var = tk.StringVar(value="No file loaded")
        ttk.Label(path_row, textvariable=self._path_var, style="Meta.TLabel").pack(
            anchor=tk.W
        )

        card = ttk.Frame(main, style="Card.TFrame", padding=20)
        card.pack(fill=tk.X, padx=28, pady=(0, 12))

        ttk.Label(card, text="Parameters", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 14))

        grid = ttk.Frame(card, style="Card.TFrame")
        grid.pack(fill=tk.X)

        ttk.Label(grid, text="Slot length", style="Field.TLabel").grid(row=0, column=0, sticky=tk.W)
        self._duration = tk.StringVar(value="60")
        dur = ttk.Combobox(
            grid,
            textvariable=self._duration,
            values=("30", "45", "60", "90"),
            width=7,
            state="readonly",
        )
        dur.grid(row=0, column=1, padx=(10, 28), sticky=tk.W)

        ttk.Label(grid, text="Search step", style="Field.TLabel").grid(row=0, column=2, sticky=tk.W)
        self._step = tk.StringVar(value="30")
        step = ttk.Combobox(
            grid,
            textvariable=self._step,
            values=("15", "30", "60"),
            width=7,
            state="readonly",
        )
        step.grid(row=0, column=3, padx=(10, 0), sticky=tk.W)

        ttk.Label(grid, text="Day window", style="Field.TLabel").grid(
            row=1, column=0, sticky=tk.W, pady=(12, 0)
        )
        win = ttk.Frame(grid, style="Card.TFrame")
        win.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(12, 0), padx=(10, 0))
        self._day_start = tk.StringVar(value="09:00")
        self._day_end = tk.StringVar(value="17:00")
        ttk.Entry(win, textvariable=self._day_start, width=7, style="Clean.TEntry").pack(
            side=tk.LEFT
        )
        ttk.Label(win, text="—", style="Dim.TLabel").pack(side=tk.LEFT, padx=8)
        ttk.Entry(win, textvariable=self._day_end, width=7, style="Clean.TEntry").pack(side=tk.LEFT)

        ttk.Label(grid, text="Show top", style="Field.TLabel").grid(
            row=1, column=4, sticky=tk.W, padx=(24, 0), pady=(12, 0)
        )
        self._top_n = tk.StringVar(value="25")
        ttk.Spinbox(
            grid,
            from_=5,
            to=100,
            textvariable=self._top_n,
            width=5,
            style="Clean.TSpinbox",
        ).grid(row=1, column=5, sticky=tk.W, pady=(12, 0), padx=(10, 0))

        action = ttk.Frame(main, style="App.TFrame", padding=(28, 4, 28, 12))
        action.pack(fill=tk.X)
        ttk.Button(
            action,
            text="Suggest office hours",
            command=self._run_suggest,
            style="Primary.TButton",
        ).pack(anchor=tk.W)

        table_outer = ttk.Frame(main, style="App.TFrame", padding=(28, 0, 28, 20))
        table_outer.pack(fill=tk.BOTH, expand=True)

        table_card = ttk.Frame(table_outer, style="Card.TFrame", padding=(0, 0, 0, 0))
        table_card.pack(fill=tk.BOTH, expand=True)

        table_head = ttk.Frame(table_card, style="Card.TFrame", padding=(16, 14, 16, 8))
        table_head.pack(fill=tk.X)
        ttk.Label(table_head, text="Ranked slots", style="Section.TLabel").pack(side=tk.LEFT)

        table_frame = ttk.Frame(table_card, style="Card.TFrame", padding=(0, 0, 8, 12))
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("rank", "coverage", "day", "start", "end")
        self._tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=16,
            selectmode=tk.BROWSE,
        )
        self._tree.heading("rank", text="#")
        self._tree.heading("coverage", text="Free")
        self._tree.heading("day", text="Day", anchor=tk.CENTER)
        self._tree.heading("start", text="Start")
        self._tree.heading("end", text="End")
        self._tree.column("rank", width=44, anchor=tk.CENTER)
        self._tree.column("coverage", width=110, anchor=tk.CENTER)
        self._tree.column("day", width=108, anchor=tk.CENTER)
        self._tree.column("start", width=88, anchor=tk.CENTER)
        self._tree.column("end", width=88, anchor=tk.CENTER)
        scroll = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self._tree.yview,
        )
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._status = tk.StringVar(value="Load a CSV of student busy times.")
        ttk.Label(
            self,
            textvariable=self._status,
            style="Status.TLabel",
            anchor=tk.W,
        ).pack(fill=tk.X, side=tk.BOTTOM)

        self._set_theme("light")

    def _set_theme(self, mode: str) -> None:
        self._theme_mode = mode
        style = ttk.Style(self)

        if mode == "dark":
            bg = "#0c0a09"
            surface = "#1c1917"
            surface_2 = "#292524"
            hairline = "#44403c"
            fg = "#fafaf9"
            muted = "#a8a29e"
            dim = "#78716c"
            field_bg = "#292524"
            tree_head = "#292524"
            row_a = "#1c1917"
            row_b = "#18181b"
            select_bg = "#e7e5e4"
            select_fg = "#1c1917"
            primary_bg = "#fafaf9"
            primary_fg = "#0c0a09"
            primary_hover = "#f5f5f4"
            ghost_hi = "#292524"
        else:
            bg = "#fafaf9"
            surface = "#ffffff"
            surface_2 = "#f5f5f4"
            hairline = "#e7e5e4"
            fg = "#1c1917"
            muted = "#78716c"
            dim = "#a8a29e"
            field_bg = "#fafaf9"
            tree_head = "#f5f5f4"
            row_a = "#ffffff"
            row_b = "#fafaf9"
            select_bg = "#292524"
            select_fg = "#fafaf9"
            primary_bg = "#1c1917"
            primary_fg = "#fafaf9"
            primary_hover = "#44403c"
            ghost_hi = "#f5f5f4"

        self.configure(bg=bg)

        try:
            hwnd = ctypes.windll.user32.GetParent(int(self.winfo_id()))
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
        style.configure("Card.TFrame", background=surface)

        style.configure(
            "Eyebrow.TLabel",
            background=bg,
            foreground=dim,
            font=("Segoe UI", 8),
        )
        style.configure(
            "Hero.TLabel",
            background=bg,
            foreground=fg,
            font=("Segoe UI", 22),
        )
        style.configure(
            "Tagline.TLabel",
            background=bg,
            foreground=muted,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Meta.TLabel",
            background=bg,
            foreground=muted,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Section.TLabel",
            background=surface,
            foreground=fg,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=surface,
            foreground=muted,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Dim.TLabel",
            background=surface,
            foreground=dim,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Status.TLabel",
            background=surface_2,
            foreground=muted,
            font=("Segoe UI", 9),
            padding=(28, 10),
        )

        style.configure(
            "TSeparator",
            background=hairline,
        )

        style.configure(
            "Clean.TEntry",
            fieldbackground=field_bg,
            foreground=fg,
            padding=6,
        )
        style.configure(
            "Clean.TSpinbox",
            fieldbackground=field_bg,
            foreground=fg,
            padding=4,
        )
        style.configure(
            "TCombobox",
            fieldbackground=field_bg,
            background=field_bg,
            foreground=fg,
            padding=5,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", field_bg)],
            foreground=[("readonly", fg)],
        )

        self.option_add("*TCombobox*Listbox.background", field_bg)
        self.option_add("*TCombobox*Listbox.foreground", fg)
        self.option_add("*TCombobox*Listbox.selectBackground", select_bg)
        self.option_add("*TCombobox*Listbox.selectForeground", select_fg)

        style.configure(
            "Primary.TButton",
            background=primary_bg,
            foreground=primary_fg,
            font=("Segoe UI", 10, "bold"),
            padding=(20, 10),
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", primary_hover), ("pressed", primary_hover)],
            foreground=[("active", primary_fg), ("pressed", primary_fg)],
        )

        style.configure(
            "Ghost.TButton",
            background=bg,
            foreground=fg,
            font=("Segoe UI", 10),
            padding=(16, 8),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", ghost_hi)],
            foreground=[("active", fg)],
        )

        style.configure(
            "Treeview",
            background=row_a,
            fieldbackground=row_a,
            foreground=fg,
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=tree_head,
            foreground=muted,
            font=("Segoe UI", 9, "bold"),
            padding=(10, 10),
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", select_bg)],
            foreground=[("selected", select_fg)],
        )

        style.configure(
            "TScrollbar",
            background=surface_2,
            troughcolor=bg,
            borderwidth=0,
            arrowsize=12,
        )
        style.map(
            "TScrollbar",
            background=[("active", hairline), ("pressed", hairline)],
        )

        if hasattr(self, "_tree"):
            self._tree.tag_configure("oddrow", background=row_a, foreground=fg)
            self._tree.tag_configure("evenrow", background=row_b, foreground=fg)

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
            self._path_var.set(f"{path.name} · {n} student{'s' if n != 1 else ''}")
            self._status.set(f"Ready — click Suggest office hours.")
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
            ranked = rank_office_hour_slots_decision_tree(
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
            row_tag = "evenrow" if i % 2 == 0 else "oddrow"
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
            f"Top {len(ranked)} slot(s) by decision-tree coverage · {total} students in file."
        )


def run_app() -> None:
    app = FacultyTimeApp()
    app.mainloop()
