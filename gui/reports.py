import json
import config
import customtkinter as ctk
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from database.sqlite import get_db


class ReportsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 12))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            title_frame,
            text="Reports",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Browse execution history, examine event listings, and export logs",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w",
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Toolbar Actions
        actions_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_row.grid(row=0, column=1, sticky="e")

        self.btn_export = ctk.CTkButton(
            actions_row,
            text="Export CSV",
            width=100,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._export_csv,
        )
        self.btn_export.pack(side="left", padx=4)

        self.btn_refresh = ctk.CTkButton(
            actions_row,
            text="Refresh",
            width=80,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._load,
        )
        self.btn_refresh.pack(side="right", padx=4)

        # ─── TABVIEW CARD CONTAINER ───
        tab_card = ctk.CTkFrame(
            self,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12,
        )
        tab_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        tabs = ctk.CTkTabview(tab_card, fg_color="transparent")
        tabs.pack(fill="both", expand=True, padx=12, pady=12)

        self._test_tab = tabs.add("Test Results")
        self._event_tab = tabs.add("Event Log")
        self._can_tab = tabs.add("CAN Log")

        self._test_scroll = ctk.CTkScrollableFrame(
            self._test_tab, fg_color="transparent"
        )
        self._test_scroll.pack(fill="both", expand=True)

        self._event_scroll = ctk.CTkScrollableFrame(
            self._event_tab, fg_color="transparent"
        )
        self._event_scroll.pack(fill="both", expand=True)

        self._can_scroll = ctk.CTkScrollableFrame(self._can_tab, fg_color="transparent")
        self._can_scroll.pack(fill="both", expand=True)

        self._load()

    def _load(self):
        self._fill_test_results()
        self._fill_events()
        self._fill_can_log()

    def _fill_test_results(self):
        for w in self._test_scroll.winfo_children():
            w.destroy()

        db = get_db()
        rows = db.execute(
            "SELECT * FROM test_results ORDER BY id DESC LIMIT 100"
        ).fetchall()

        # Header Row
        header = ctk.CTkFrame(
            self._test_scroll, fg_color=("gray95", "gray25"), corner_radius=6
        )
        header.pack(fill="x", pady=(0, 6))
        for col, w in [
            ("Timestamp", 140),
            ("Test Name", 200),
            ("Outcome", 70),
            ("Summary Steps Details", 0),
        ]:
            ctk.CTkLabel(
                header,
                text=col,
                width=w,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=("#1f538d", "#60a5fa"),
            ).pack(side="left", padx=10, pady=6)

        for i, r in enumerate(rows):
            row_bg = ("gray98", "gray24") if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._test_scroll, fg_color=row_bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            outcome = r["status"]
            color = "#10b981" if outcome == "PASS" else "#ef4444"
            steps = json.loads(r["details"] or "[]")
            step_str = "  |  ".join(
                f"[{s['status']}] {s['description']}" for s in steps[:3]
            )

            # Timestamp cell
            ctk.CTkLabel(
                row,
                text=r["timestamp"][:19],
                width=140,
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=("gray40", "gray60"),
            ).pack(side="left", padx=10, pady=4)

            # Test Name cell
            ctk.CTkLabel(
                row,
                text=r["test_name"],
                width=200,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12),
            ).pack(side="left", padx=10, pady=4)

            # Outcome badge
            ctk.CTkLabel(
                row,
                text=f"[{outcome}]",
                width=70,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=color,
            ).pack(side="left", padx=10, pady=4)

            # Details
            ctk.CTkLabel(
                row,
                text=step_str,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=("gray50", "gray40"),
            ).pack(side="left", padx=10, pady=4, fill="x", expand=True)

    def _fill_events(self):
        for w in self._event_scroll.winfo_children():
            w.destroy()

        db = get_db()
        rows = db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()

        # Header Row
        header = ctk.CTkFrame(
            self._event_scroll, fg_color=("gray95", "gray25"), corner_radius=6
        )
        header.pack(fill="x", pady=(0, 6))
        for col, w in [
            ("Timestamp", 140),
            ("Severity", 80),
            ("Event Description Message", 0),
        ]:
            ctk.CTkLabel(
                header,
                text=col,
                width=w,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=("#1f538d", "#60a5fa"),
            ).pack(side="left", padx=10, pady=6)

        for i, r in enumerate(rows):
            row_bg = ("gray98", "gray24") if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._event_scroll, fg_color=row_bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            is_crit = r["severity"].lower() == "critical"
            color = "#ef4444" if is_crit else ("gray20", "white")
            severity_lbl = f"[{r['severity'].upper()}]"

            # Timestamp
            ctk.CTkLabel(
                row,
                text=r["timestamp"][:19],
                width=140,
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=("gray40", "gray60"),
            ).pack(side="left", padx=10, pady=4)

            # Severity
            ctk.CTkLabel(
                row,
                text=severity_lbl,
                width=80,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color="#ef4444" if is_crit else ("#1f538d", "#60a5fa"),
            ).pack(side="left", padx=10, pady=4)

            # Message
            ctk.CTkLabel(
                row,
                text=r["message"],
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=color,
            ).pack(side="left", padx=10, pady=4, fill="x", expand=True)

    def _convert_ts(self, utc_str: str) -> str:
        """Convert a stored UTC ISO timestamp string to the configured local timezone."""
        try:
            # Timestamps are stored as plain UTC strings without 'Z' or offset
            dt_utc = datetime.fromisoformat(utc_str).replace(tzinfo=timezone.utc)
            tz = ZoneInfo(config.TIMEZONE)
            dt_local = dt_utc.astimezone(tz)
            return dt_local.strftime("%H:%M:%S")
        except (ValueError, ZoneInfoNotFoundError):
            # Fallback: slice raw string
            return utc_str[11:19]

    def _fill_can_log(self):
        for w in self._can_scroll.winfo_children():
            w.destroy()

        db = get_db()
        rows = db.execute("SELECT * FROM can_log ORDER BY id DESC LIMIT 200").fetchall()

        # Header Row — show the active timezone in the column name
        tz_label = config.TIMEZONE
        header = ctk.CTkFrame(
            self._can_scroll, fg_color=("gray95", "gray25"), corner_radius=6
        )
        header.pack(fill="x", pady=(0, 6))
        for col, w in [
            (f"Time ({tz_label})", 120),
            ("CAN ID", 100),
            ("DLC", 60),
            ("Data Payload Bytes (hex)", 0),
        ]:
            ctk.CTkLabel(
                header,
                text=col,
                width=w,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=("#1f538d", "#60a5fa"),
            ).pack(side="left", padx=10, pady=6)

        for i, r in enumerate(rows):
            row_bg = ("gray98", "gray24") if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._can_scroll, fg_color=row_bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            # Timestamp — converted to selected timezone
            ctk.CTkLabel(
                row,
                text=self._convert_ts(r["timestamp"]),
                width=120,
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12),
            ).pack(side="left", padx=10, pady=4)

            # CAN ID
            ctk.CTkLabel(
                row,
                text=r["can_id"],
                width=100,
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=("#1d4ed8", "#60a5fa"),
            ).pack(side="left", padx=10, pady=4)

            # DLC
            ctk.CTkLabel(
                row,
                text=str(r["dlc"]),
                width=60,
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12),
            ).pack(side="left", padx=10, pady=4)

            # Hex Data
            ctk.CTkLabel(
                row,
                text=r["data"],
                anchor="w",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=("gray40", "gray60"),
            ).pack(side="left", padx=10, pady=4, fill="x", expand=True)

    def _export_csv(self):
        from tkinter import filedialog
        import csv

        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        db = get_db()
        rows = db.execute("SELECT * FROM test_results ORDER BY id DESC").fetchall()
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "timestamp", "test_name", "status", "details"])
            for r in rows:
                writer.writerow(
                    [r["id"], r["timestamp"], r["test_name"], r["status"], r["details"]]
                )
