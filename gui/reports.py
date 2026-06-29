import json
import customtkinter as ctk
from database.sqlite import get_db


class ReportsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Reports", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Refresh", width=80, command=self._load).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Export CSV", width=100, command=self._export_csv).pack(side="right", padx=4)

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=8)
        self._test_tab = tabs.add("Test Results")
        self._event_tab = tabs.add("Event Log")
        self._can_tab = tabs.add("CAN Log")

        self._test_scroll = ctk.CTkScrollableFrame(self._test_tab)
        self._test_scroll.pack(fill="both", expand=True)
        self._event_scroll = ctk.CTkScrollableFrame(self._event_tab)
        self._event_scroll.pack(fill="both", expand=True)
        self._can_scroll = ctk.CTkScrollableFrame(self._can_tab)
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
        rows = db.execute("SELECT * FROM test_results ORDER BY id DESC LIMIT 100").fetchall()
        header = ctk.CTkFrame(self._test_scroll)
        header.pack(fill="x")
        for col, w in [("Time", 140), ("Test", 200), ("Result", 70), ("Steps", 360)]:
            ctk.CTkLabel(header, text=col, width=w, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
        for i, r in enumerate(rows):
            row = ctk.CTkFrame(self._test_scroll,
                               fg_color=("gray85", "gray22") if i % 2 == 0 else "transparent")
            row.pack(fill="x", pady=1)
            color = "green" if r["status"] == "PASS" else "red"
            steps = json.loads(r["details"] or "[]")
            step_str = "  |  ".join(f"[{s['status']}] {s['description']}" for s in steps[:3])
            for text, width, tc in [
                (r["timestamp"][:19], 140, "white"),
                (r["test_name"], 200, "white"),
                (r["status"], 70, color),
                (step_str, 360, "gray"),
            ]:
                ctk.CTkLabel(row, text=text, width=width, anchor="w", text_color=tc).pack(side="left", padx=4)

    def _fill_events(self):
        for w in self._event_scroll.winfo_children():
            w.destroy()
        db = get_db()
        rows = db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
        for i, r in enumerate(rows):
            row = ctk.CTkFrame(self._event_scroll,
                               fg_color=("gray85", "gray22") if i % 2 == 0 else "transparent")
            row.pack(fill="x", pady=1)
            color = "red" if r["severity"] == "critical" else "white"
            for text, width in [
                (r["timestamp"][:19], 140),
                (r["severity"].upper(), 70),
                (r["message"], 380),
            ]:
                ctk.CTkLabel(row, text=text, width=width, anchor="w", text_color=color).pack(side="left", padx=4)

    def _fill_can_log(self):
        for w in self._can_scroll.winfo_children():
            w.destroy()
        db = get_db()
        rows = db.execute("SELECT * FROM can_log ORDER BY id DESC LIMIT 200").fetchall()
        for i, r in enumerate(rows):
            row = ctk.CTkFrame(self._can_scroll,
                               fg_color=("gray85", "gray22") if i % 2 == 0 else "transparent")
            row.pack(fill="x", pady=1)
            for text, width in [
                (r["timestamp"][11:19], 80),
                (r["can_id"], 80),
                (str(r["dlc"]), 40),
                (r["data"], 260),
            ]:
                ctk.CTkLabel(row, text=text, width=width, anchor="w").pack(side="left", padx=4)

    def _export_csv(self):
        from tkinter import filedialog
        import csv
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        db = get_db()
        rows = db.execute("SELECT * FROM test_results ORDER BY id DESC").fetchall()
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "timestamp", "test_name", "status", "details"])
            for r in rows:
                writer.writerow([r["id"], r["timestamp"], r["test_name"], r["status"], r["details"]])
