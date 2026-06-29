"""
Version History Dialog
Displays commit history for the current branch.
Allows copying commit hash to clipboard.
"""
from __future__ import annotations

import customtkinter as ctk
from services.git_service import git_service


class HistoryDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Version History")
        self.geometry("860x480")
        self.resizable(True, True)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Version History",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Refresh", width=80,
                      command=self._load).pack(side="right")

        # Header row
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=16)
        for col, w in [("Hash", 70), ("Version/Message", 300),
                       ("Author", 140), ("Date", 130), ("Branch", 120)]:
            ctk.CTkLabel(header, text=col, width=w, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="Actions", width=80, anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)

        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.pack(fill="both", expand=True, padx=16, pady=8)

        self._status = ctk.CTkLabel(self, text="", text_color="gray")
        self._status.pack(pady=4)

        self._load()

    def _load(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        try:
            records = git_service.get_history(limit=60)
        except Exception as exc:
            ctk.CTkLabel(self._scroll, text=f"Could not load history: {exc}",
                         text_color="red").pack(pady=20)
            return

        if not records:
            ctk.CTkLabel(self._scroll, text="No commits found.",
                         text_color="gray").pack(pady=20)
            return

        for i, rec in enumerate(records):
            row = ctk.CTkFrame(
                self._scroll,
                fg_color=("gray85", "gray22") if i % 2 == 0 else "transparent",
            )
            row.pack(fill="x", pady=1)
            for text, width in [
                (rec.short_hash, 70),
                (rec.message[:45] + ("…" if len(rec.message) > 45 else ""), 300),
                (rec.author[:20], 140),
                (rec.date, 130),
                (rec.branch[:18], 120),
            ]:
                ctk.CTkLabel(row, text=text, width=width, anchor="w").pack(
                    side="left", padx=4)

            ctk.CTkButton(
                row, text="Copy Hash", width=80, height=24,
                fg_color="gray40",
                command=lambda h=rec.hash: self._copy(h),
            ).pack(side="left", padx=4)

    def _copy(self, hash_str: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(hash_str)
        self._status.configure(text=f"Copied: {hash_str[:7]}", text_color="green")
