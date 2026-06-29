"""
Commit Dialog
Collects commit message, version, and description before pushing.
Auto-generates a conventional commit suggestion.
"""
from __future__ import annotations

import customtkinter as ctk
from core.project import project


class CommitDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, branch: str) -> None:
        super().__init__(parent)
        self.title("Commit & Push")
        self.geometry("500x400")
        self.resizable(False, False)
        self.grab_set()

        self._branch = branch
        self.commit_message: str = ""
        self.confirmed: bool = False
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Commit Details",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text=f"Branch:  {self._branch}",
                     text_color="gray").pack(pady=(0, 12))

        form = ctk.CTkFrame(self)
        form.pack(padx=24, fill="x")

        # Version
        ctk.CTkLabel(form, text="Version", anchor="w").grid(
            row=0, column=0, padx=8, pady=8, sticky="w")
        self._version = ctk.CTkEntry(form, width=180, placeholder_text="1.0.0")
        self._version.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        # Commit message
        ctk.CTkLabel(form, text="Commit Message", anchor="w").grid(
            row=1, column=0, padx=8, pady=8, sticky="nw")
        self._msg_entry = ctk.CTkEntry(form, width=320)
        self._msg_entry.grid(row=1, column=1, padx=8, pady=8)
        self._msg_entry.insert(0, self._suggest_message())

        # Description
        ctk.CTkLabel(form, text="Description", anchor="w").grid(
            row=2, column=0, padx=8, pady=8, sticky="nw")
        self._desc = ctk.CTkTextbox(form, width=320, height=80)
        self._desc.grid(row=2, column=1, padx=8, pady=8)

        ctk.CTkButton(self, text="Restore Suggestion",
                      fg_color="gray40", width=160,
                      command=self._restore_suggestion).pack(pady=4)

        self._status = ctk.CTkLabel(self, text="", text_color="red")
        self._status.pack()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Cancel", width=100, fg_color="gray40",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Commit & Push", width=140,
                      fg_color="green", command=self._confirm).pack(side="left", padx=8)

    def _suggest_message(self) -> str:
        branch = self._branch.replace("/", "_").replace("-", "_")
        name = project.name.replace(" ", "_")
        return f"feat({branch}): update {name} test task"

    def _restore_suggestion(self) -> None:
        self._msg_entry.delete(0, "end")
        self._msg_entry.insert(0, self._suggest_message())

    def _confirm(self) -> None:
        msg = self._msg_entry.get().strip()
        if not msg:
            self._status.configure(text="Commit message is required.")
            return
        desc = self._desc.get("1.0", "end").strip()
        version = self._version.get().strip()
        full = msg
        if version:
            full = f"[v{version}] {full}"
        if desc:
            full = f"{full}\n\n{desc}"
        self.commit_message = full
        self.confirmed = True
        self.destroy()
