"""
Repository Selection Dialog
Allows the user to open an existing local repo or clone from GitHub.
Remembers recently used repositories in project config.
"""

from __future__ import annotations

import json
import os
from tkinter import filedialog

import customtkinter as ctk
from services.credential_manager import credential_manager
from services.git_service import git_service

_RECENT_FILE = "git_recent_repos.json"
_MAX_RECENT = 8


def _load_recent() -> list[str]:
    if os.path.exists(_RECENT_FILE):
        try:
            return json.load(open(_RECENT_FILE))
        except Exception:
            pass
    return []


def _save_recent(path: str) -> None:
    recent = [p for p in _load_recent() if p != path]
    recent.insert(0, path)
    with open(_RECENT_FILE, "w") as f:
        json.dump(recent[:_MAX_RECENT], f)


class RepoDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Select Repository")
        self.geometry("560x420")
        self.resizable(False, False)
        self.grab_set()

        self.selected_path: str = ""
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Repository Selection", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 4))

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=20, pady=8)
        local_tab = tabs.add("Open Local")
        clone_tab = tabs.add("Clone from GitHub")

        self._build_local_tab(local_tab)
        self._build_clone_tab(clone_tab)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=8)
        ctk.CTkButton(
            btn_row, text="Cancel", width=100, fg_color="gray40", command=self.destroy
        ).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Open", width=100, command=self._confirm).pack(
            side="left", padx=8
        )

    # ------------------------------------------------------------------ #
    #  Local tab                                                           #
    # ------------------------------------------------------------------ #
    def _build_local_tab(self, parent: ctk.CTkFrame) -> None:
        ctk.CTkLabel(parent, text="Recent Repositories", anchor="w").pack(
            anchor="w", padx=8, pady=(12, 4)
        )

        self._recent_var = ctk.StringVar()
        recent = _load_recent()
        self._recent_menu = ctk.CTkOptionMenu(
            parent,
            values=recent if recent else ["No recent repositories"],
            variable=self._recent_var,
            width=460,
        )
        self._recent_menu.pack(padx=8, pady=4)
        if recent:
            self._recent_var.set(recent[0])

        ctk.CTkLabel(
            parent,
            text="Or browse for a repository folder:",
            text_color="gray",
            anchor="w",
        ).pack(anchor="w", padx=8, pady=(12, 4))

        browse_row = ctk.CTkFrame(parent, fg_color="transparent")
        browse_row.pack(fill="x", padx=8)
        self._path_label = ctk.CTkLabel(
            browse_row,
            text="No folder selected",
            text_color="gray",
            anchor="w",
            width=360,
        )
        self._path_label.pack(side="left")
        ctk.CTkButton(browse_row, text="Browse", width=80, command=self._browse).pack(
            side="left", padx=8
        )

        self._local_status = ctk.CTkLabel(parent, text="", text_color="red")
        self._local_status.pack(pady=4)

    def _browse(self) -> None:
        path = filedialog.askdirectory(title="Select Git Repository Folder")
        if path:
            self._browsed_path = path
            self._path_label.configure(text=path, text_color="white")

    # ------------------------------------------------------------------ #
    #  Clone tab                                                           #
    # ------------------------------------------------------------------ #
    def _build_clone_tab(self, parent: ctk.CTkFrame) -> None:
        _, _ = credential_manager.load()

        ctk.CTkLabel(parent, text="Repository URL (HTTPS)", anchor="w").pack(
            anchor="w", padx=8, pady=(12, 4)
        )
        self._clone_url = ctk.CTkEntry(
            parent, width=460, placeholder_text="https://github.com/user/repo.git"
        )
        self._clone_url.pack(padx=8, pady=4)

        ctk.CTkLabel(parent, text="Clone into folder", anchor="w").pack(
            anchor="w", padx=8, pady=(8, 4)
        )
        dest_row = ctk.CTkFrame(parent, fg_color="transparent")
        dest_row.pack(fill="x", padx=8)
        self._dest_label = ctk.CTkLabel(
            dest_row,
            text="No folder selected",
            text_color="gray",
            anchor="w",
            width=360,
        )
        self._dest_label.pack(side="left")
        ctk.CTkButton(
            dest_row, text="Browse", width=80, command=self._browse_dest
        ).pack(side="left", padx=8)

        ctk.CTkButton(parent, text="Clone Repository", command=self._clone).pack(
            pady=12
        )

        self._clone_status = ctk.CTkLabel(parent, text="", text_color="gray")
        self._clone_status.pack()

        self._dest_path: str = ""

    def _browse_dest(self) -> None:
        path = filedialog.askdirectory(title="Select Destination Folder")
        if path:
            self._dest_path = path
            self._dest_label.configure(text=path, text_color="white")

    def _clone(self) -> None:
        url = self._clone_url.get().strip()
        if not url or not self._dest_path:
            self._clone_status.configure(
                text="URL and destination folder required.", text_color="red"
            )
            return
        username, pat = credential_manager.load()
        if not username or not pat:
            self._clone_status.configure(
                text="No credentials stored. Login first.", text_color="red"
            )
            return
        self._clone_status.configure(text="Cloning...", text_color="gray")
        self.update()
        try:
            repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
            dest = os.path.join(self._dest_path, repo_name)
            git_service.clone_repo(url, dest, username, pat)
            self.selected_path = dest
            _save_recent(dest)
            self._clone_status.configure(text=f"Cloned to: {dest}", text_color="green")
        except Exception as exc:
            self._clone_status.configure(text=f"Clone failed: {exc}", text_color="red")

    # ------------------------------------------------------------------ #
    #  Confirm                                                             #
    # ------------------------------------------------------------------ #
    def _confirm(self) -> None:
        # Priority: browsed path > recent selection > clone result
        path = (
            getattr(self, "_browsed_path", "")
            or self._recent_var.get()
            or self.selected_path
        )
        if not path or path == "No recent repositories":
            return
        try:
            git_service.open_repo(path)
            self.selected_path = path
            _save_recent(path)
            self.destroy()
        except ValueError as exc:
            if hasattr(self, "_local_status"):
                self._local_status.configure(text=str(exc))
