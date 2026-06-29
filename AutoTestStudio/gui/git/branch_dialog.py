"""
Branch Selection Dialog
Lists existing branches and allows creating a new feature branch.
Pushes to main/master are blocked at the service layer and here.
"""
from __future__ import annotations

import customtkinter as ctk
from services.git_service import git_service

_PROTECTED = {"main", "master"}


class BranchDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Branch Selection")
        self.geometry("440x400")
        self.resizable(False, False)
        self.grab_set()

        self.selected_branch: str = ""
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Branch Management",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(self, text="Never push directly to main or master.",
                     text_color="gray").pack(pady=(0, 12))

        # Current branch indicator
        try:
            current = git_service.current_branch()
        except Exception:
            current = "unknown"
        ctk.CTkLabel(self, text=f"Current Branch:  {current}",
                     font=ctk.CTkFont(weight="bold")).pack(pady=4)

        # Branch list
        ctk.CTkLabel(self, text="Existing Branches", anchor="w").pack(
            anchor="w", padx=24, pady=(12, 4))

        self._branch_var = ctk.StringVar()
        branches = self._safe_branches()
        self._radio_frame = ctk.CTkScrollableFrame(self, height=120)
        self._radio_frame.pack(fill="x", padx=24)

        for b in branches:
            is_protected = b in _PROTECTED
            label = f"{b}  [protected — read only]" if is_protected else b
            rb = ctk.CTkRadioButton(
                self._radio_frame, text=label,
                variable=self._branch_var, value=b,
                state="disabled" if is_protected else "normal",
            )
            rb.pack(anchor="w", pady=2)
        if branches:
            # Pre-select first non-protected branch
            for b in branches:
                if b not in _PROTECTED:
                    self._branch_var.set(b)
                    break

        # Create new branch
        sep = ctk.CTkFrame(self, height=1, fg_color="gray40")
        sep.pack(fill="x", padx=24, pady=10)

        ctk.CTkLabel(self, text="Create New Branch", anchor="w",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=24)

        new_row = ctk.CTkFrame(self, fg_color="transparent")
        new_row.pack(fill="x", padx=24, pady=6)
        self._new_branch = ctk.CTkEntry(new_row, width=280,
                                        placeholder_text="feature/my-test-branch")
        self._new_branch.pack(side="left", padx=(0, 8))
        ctk.CTkButton(new_row, text="Create", width=80,
                      command=self._create_branch).pack(side="left")

        self._status = ctk.CTkLabel(self, text="", text_color="red")
        self._status.pack(pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=8)
        ctk.CTkButton(btn_row, text="Cancel", width=100, fg_color="gray40",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Select Branch", width=120,
                      command=self._confirm).pack(side="left", padx=8)

    def _safe_branches(self) -> list[str]:
        try:
            return git_service.list_branches()
        except Exception:
            return []

    def _create_branch(self) -> None:
        name = self._new_branch.get().strip()
        if not name:
            self._status.configure(text="Enter a branch name.")
            return
        if name in _PROTECTED:
            self._status.configure(
                text=f"Cannot create protected branch '{name}'.", text_color="red")
            return
        try:
            git_service.create_branch(name)
            # Add to radio list
            rb = ctk.CTkRadioButton(
                self._radio_frame, text=name,
                variable=self._branch_var, value=name,
            )
            rb.pack(anchor="w", pady=2)
            self._branch_var.set(name)
            self._status.configure(text=f"Branch '{name}' created.", text_color="green")
        except ValueError as exc:
            self._status.configure(text=str(exc), text_color="red")

    def _confirm(self) -> None:
        branch = self._branch_var.get()
        if not branch or branch in _PROTECTED:
            self._status.configure(
                text="Select a valid feature branch (not main/master).", text_color="red")
            return
        self.selected_branch = branch
        self.destroy()
