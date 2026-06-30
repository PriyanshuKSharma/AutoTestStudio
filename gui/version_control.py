"""
Version Control Panel
Top-level GUI panel for the Version Control feature.
Wires together: Login -> Repo -> Branch -> Commit -> Push.
Local Save and GitHub Save are completely separate actions.
"""
from __future__ import annotations

import customtkinter as ctk
import os

from core.project import project
from services.credential_manager import credential_manager
from services.git_service import git_service, PushResult
from gui.git.login_dialog import LoginDialog
from gui.git.repo_dialog import RepoDialog
from gui.git.branch_dialog import BranchDialog
from gui.git.commit_dialog import CommitDialog
from gui.git.history_dialog import HistoryDialog
from gui.git.status_bar import GitStatusBar


class VersionControlPanel(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame) -> None:
        super().__init__(parent, fg_color="transparent")
        self._branch: str = ""
        self._last_commit: str = ""
        self._build()

    # ------------------------------------------------------------------ #
    #  Layout                                                            #
    # ------------------------------------------------------------------ #
    def _build(self) -> None:
        # Scroll container to keep layout cohesive
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=24, pady=20)
        self.scroll_container.columnconfigure(0, weight=1)

        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Version Control",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Track configuration changes, inspect history logs, and push updates to remote git repositories",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Status bar
        self._status_bar = GitStatusBar(self.scroll_container, height=32)
        self._status_bar.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # ─── PROJECT INFO CARD ───
        info_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        info_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        info_card.columnconfigure(0, weight=1)

        info_inner = ctk.CTkFrame(info_card, fg_color="transparent")
        info_inner.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            info_inner,
            text="REPOSITORY DETAILS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        divider1 = ctk.CTkFrame(info_inner, height=1, fg_color=("gray90", "gray28"))
        divider1.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # Metadata rows
        metadata = [
            ("Project Name:", project.name, "_proj_label", "Segoe UI", True),
            ("Git Repository:", "No repository selected", "_repo_label", "Consolas", False),
            ("Active Branch:", "None", "_branch_label", "Consolas", False),
            ("GitHub Account:", self._stored_username(), "_user_label", "Segoe UI", False)
        ]

        for i, (label_text, default_val, attr_name, font_fam, is_bold) in enumerate(metadata):
            lbl = ctk.CTkLabel(
                info_inner,
                text=label_text,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=("gray50", "gray40"),
                anchor="w",
                width=130
            )
            lbl.grid(row=i+2, column=0, sticky="w", pady=6)

            val_font = ctk.CTkFont(family=font_fam, size=13, weight="bold" if is_bold else "normal")
            val_lbl = ctk.CTkLabel(
                info_inner,
                text=default_val,
                font=val_font,
                anchor="w"
            )
            val_lbl.grid(row=i+2, column=1, sticky="w", pady=6)
            setattr(self, attr_name, val_lbl)

            if attr_name == "_repo_label" and default_val != "No repository selected":
                val_lbl.configure(text_color=("black", "white"))
            elif attr_name == "_branch_label" and default_val != "None":
                val_lbl.configure(text_color=("#1d4ed8", "#60a5fa"))
            elif attr_name == "_user_label" and default_val != "Not logged in":
                val_lbl.configure(text_color="#10b981")

        info_inner.columnconfigure(1, weight=1)

        # ─── ACTIONS CARD ───
        btn_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        btn_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        btn_inner = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_inner.pack(padx=20, pady=16, fill="both")

        # Row 1 Actions: Save options
        btn_row1 = ctk.CTkFrame(btn_inner, fg_color="transparent")
        btn_row1.pack(fill="x", pady=(0, 10))

        self.btn_save_local = ctk.CTkButton(
            btn_row1,
            text="Save Locally",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._save_local,
            height=36
        )
        self.btn_save_local.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_save_github = ctk.CTkButton(
            btn_row1,
            text="Push to GitHub",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._save_to_github,
            height=36
        )
        self.btn_save_github.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Row 2 Actions: Git branch and repository select
        btn_row2 = ctk.CTkFrame(btn_inner, fg_color="transparent")
        btn_row2.pack(fill="x")

        self.btn_select_repo = ctk.CTkButton(
            btn_row2,
            text="Select Repository",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._select_repo,
            height=32
        )
        self.btn_select_repo.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_branch = ctk.CTkButton(
            btn_row2,
            text="Select Branch",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._change_branch,
            height=32
        )
        self.btn_branch.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_history = ctk.CTkButton(
            btn_row2,
            text="History Log",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._show_history,
            height=32
        )
        self.btn_history.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_logout = ctk.CTkButton(
            btn_row2,
            text="Logout",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self._logout,
            height=32,
            width=90
        )
        self.btn_logout.pack(side="right", padx=(12, 0))

        # Status text row
        self._msg_label = ctk.CTkLabel(
            self.scroll_container,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        self._msg_label.grid(row=4, column=0, sticky="w", padx=4, pady=8)

    # ------------------------------------------------------------------ #
    #  Actions                                                           #
    # ------------------------------------------------------------------ #
    def _save_local(self) -> None:
        """Save project locally — no Git operations."""
        try:
            project.name = self._proj_label.cget("text")
            project.save()
            self._status_bar.set_local_saved()
            self._show_message("[Success] Saved configuration files locally.", "green")
        except Exception as exc:
            self._show_message(f"Save failed: {exc}", "red")

    def _save_to_github(self) -> None:
        """Full GitHub workflow: login -> repo -> branch -> commit -> push."""
        # Step 1: Ensure credentials
        if not self._ensure_login():
            return

        # Step 2: Ensure repo is open
        if not git_service.is_open:
            self._select_repo()
            if not git_service.is_open:
                self._show_message("No repository selected. Aborting push operation.", "red")
                return

        # Step 3: Ensure branch
        if not self._branch:
            self._change_branch()
            if not self._branch:
                self._show_message("No active branch selected. Aborting push operation.", "red")
                return

        # Step 4: Commit dialog
        dlg = CommitDialog(self, self._branch)
        self.wait_window(dlg)
        if not dlg.confirmed:
            return

        # Step 5: Save locally first
        project.save()
        self._status_bar.set_local_saved()

        # Step 6: Push
        username, pat = credential_manager.load()
        self._show_message("Pushing commits to remote GitHub repository...", "gray")
        self.update()

        result: PushResult = git_service.full_workflow(
            branch=self._branch,
            commit_message=dlg.commit_message,
            username=username,
            pat=pat,
        )

        if result.success:
            self._last_commit = result.commit_hash
            self._status_bar.set_synced(result.branch, result.commit_hash)
            self._branch_label.configure(text=result.branch, text_color=("#1d4ed8", "#60a5fa"))
            self._show_message(
                f"[Success] Push complete. Branch: {result.branch} | Commit: {result.commit_hash} | Repo: {result.repo_name}",
                "green",
            )
        else:
            self._show_message(f"Push failed: {result.error}", "red")

    def _select_repo(self) -> None:
        dlg = RepoDialog(self)
        self.wait_window(dlg)
        if dlg.selected_path:
            self._repo_label.configure(
                text=git_service.repo_name, text_color=("black", "white"))
            self._show_message(f"[Repo] Opened repository path: {dlg.selected_path}", "green")

    def _change_branch(self) -> None:
        if not git_service.is_open:
            self._show_message("Please select and open a repository first.", "orange")
            return
        dlg = BranchDialog(self)
        self.wait_window(dlg)
        if dlg.selected_branch:
            self._branch = dlg.selected_branch
            self._branch_label.configure(
                text=self._branch, text_color=("#1d4ed8", "#60a5fa"))
            self._status_bar.set_not_synced()

    def _show_history(self) -> None:
        if not git_service.is_open:
            self._show_message("Please select and open a repository first.", "orange")
            return
        HistoryDialog(self)

    def _logout(self) -> None:
        credential_manager.clear()
        self._user_label.configure(text="Not logged in", text_color="gray")
        self._show_message("Logged out. Keys and tokens cleared from credentials store.", "gray")

    # ------------------------------------------------------------------ #
    #  Helpers                                                           #
    # ------------------------------------------------------------------ #
    def _ensure_login(self) -> bool:
        """Return True if valid credentials exist or user logs in successfully."""
        if credential_manager.has_credentials():
            username, _ = credential_manager.load()
            self._user_label.configure(text=username, text_color="#10b981")
            return True
        dlg = LoginDialog(self)
        self.wait_window(dlg)
        if dlg.success:
            username, _ = credential_manager.load()
            self._user_label.configure(text=username, text_color="#10b981")
            return True
        self._show_message("GitHub authentication token is required.", "red")
        return False

    def _stored_username(self) -> str:
        username, _ = credential_manager.load()
        return username if username else "Not logged in"

    def _show_message(self, text: str, color: str = "gray") -> None:
        self._msg_label.configure(text=text, text_color=color)
