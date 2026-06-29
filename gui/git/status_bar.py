"""
GitStatusBar
Reusable widget showing local save status and GitHub sync status.
Embed in any panel with status_bar.pack() or status_bar.grid().
"""
from __future__ import annotations

import customtkinter as ctk


class GitStatusBar(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, **kwargs) -> None:
        super().__init__(parent, fg_color=("gray88", "gray18"), **kwargs)
        self._local_lbl = ctk.CTkLabel(
            self, text="  Local:  Not Saved", text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self._local_lbl.pack(side="left", padx=(12, 24))

        self._sync_lbl = ctk.CTkLabel(
            self, text="GitHub:  Not Synced", text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self._sync_lbl.pack(side="left")

        self._branch_lbl = ctk.CTkLabel(self, text="", text_color="gray",
                                         font=ctk.CTkFont(size=12))
        self._branch_lbl.pack(side="left", padx=(24, 4))

        self._commit_lbl = ctk.CTkLabel(self, text="", text_color="gray",
                                         font=ctk.CTkFont(size=12))
        self._commit_lbl.pack(side="left")

    def set_local_saved(self) -> None:
        self._local_lbl.configure(text="  Local:  Saved", text_color="green")

    def set_not_saved(self) -> None:
        self._local_lbl.configure(text="  Local:  Unsaved changes", text_color="orange")

    def set_synced(self, branch: str, commit_hash: str) -> None:
        self._sync_lbl.configure(text="GitHub:  Synced", text_color="green")
        self._branch_lbl.configure(text=f"Branch: {branch}", text_color="cyan")
        self._commit_lbl.configure(text=f"Commit: {commit_hash}", text_color="gray")

    def set_not_synced(self) -> None:
        self._sync_lbl.configure(text="GitHub:  Not Synced", text_color="orange")
        self._branch_lbl.configure(text="")
        self._commit_lbl.configure(text="")
