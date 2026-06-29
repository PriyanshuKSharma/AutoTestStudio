"""
Version Control Panel
Top-level GUI panel for the Version Control feature.
Wires together: Login → Repo → Branch → Commit → Push.
Local Save and GitHub Save are completely separate actions.
"""
from __future__ import annotations

import customtkinter as ctk

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
    #  Layout                                                              #
    # ------------------------------------------------------------------ #
    def _build(self) -> None:
        # Title
        ctk.CTkLabel(
            self, text="Version Control",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(
            self, text="Manage test task versions with GitHub integration.",
            text_color="gray",
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # Status bar
        self._status_bar = GitStatusBar(self, height=32)
        self._status_bar.pack(fill="x", padx=24, pady=(0, 16))

        # Main card
        card = ctk.CTkFrame(self)
        card.pack(padx=24, pady=8, fill="x")

        # Project info
        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(info_row, text="Project:", width=100, anchor="w").pack(side="left")
        self._proj_label = ctk.CTkLabel(
            info_row, text=project.name, font=ctk.CTkFont(weight="bold"))
        self._proj_label.pack(side="left")

        repo_row = ctk.CTkFrame(card, fg_color="transparent")
        repo_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(repo_row, text="Repository:", width=100, anchor="w").pack(side="left")
        self._repo_label = ctk.CTkLabel(repo_row, text="No repository selected",
                                         text_color="gray")
        self._repo_label.pack(side="left")

        branch_row = ctk.CTkFrame(card, fg_color="transparent")
        branch_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(branch_row, text="Branch:", width=100, anchor="w").pack(side="left")
        self._branch_label = ctk.CTkLabel(branch_row, text="None",
                                           text_color="gray")
        self._branch_label.pack(side="left")

        user_row = ctk.CTkFrame(card, fg_color="transparent")
        user_row.pack(fill="x", padx=16, pady=(4, 16))
        ctk.CTkLabel(user_row, text="GitHub User:", width=100, anchor="w").pack(side="left")
        self._user_label = ctk.CTkLabel(user_row, text=self._stored_username(),
                                         text_color="gray")
        self._user_label.pack(side="left")

        # Action buttons
        btn_card = ctk.CTkFrame(self)
        btn_card.pack(padx=24, pady=8, fill="x")
        ctk.CTkLabel(btn_card, text="Actions",
                     font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=16, pady=(12, 8))

        btn_row1 = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_row1.pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            btn_row1, text="Save Locally", width=160, height=40,
            command=self._save_local,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row1, text="Save to GitHub", width=160, height=40,
            fg_color="#1f6aa5",
            command=self._save_to_github,
        ).pack(side="left", padx=8)

        btn_row2 = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_row2.pack(fill="x", padx=16, pady=(4, 16))

        ctk.CTkButton(
            btn_row2, text="Select Repository", width=160,
            fg_color="gray40", command=self._select_repo,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row2, text="Change Branch", width=160,
            fg_color="gray40", command=self._change_branch,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row2, text="Version History", width=160,
            fg_color="gray40", command=self._show_history,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row2, text="Logout", width=100,
            fg_color="gray30", command=self._logout,
        ).pack(side="right", padx=8)

        # Message area
        self._msg_label = ctk.CTkLabel(self, text="", text_color="gray")
        self._msg_label.pack(padx=24, pady=8)

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #
    def _save_local(self) -> None:
        """Save project locally — no Git operations."""
        try:
            project.name = self._proj_label.cget("text")
            project.save()
            self._status_bar.set_local_saved()
            self._show_message("Project saved locally.", "green")
        except Exception as exc:
            self._show_message(f"Save failed: {exc}", "red")

    def _save_to_github(self) -> None:
        """Full GitHub workflow: login → repo → branch → commit → push."""
        # Step 1: Ensure credentials
        if not self._ensure_login():
            return

        # Step 2: Ensure repo is open
        if not git_service.is_open:
            self._select_repo()
            if not git_service.is_open:
                self._show_message("No repository selected. Aborting.", "red")
                return

        # Step 3: Ensure branch
        if not self._branch:
            self._change_branch()
            if not self._branch:
                self._show_message("No branch selected. Aborting.", "red")
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
        self._show_message("Pushing to GitHub...", "gray")
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
            self._branch_label.configure(text=result.branch, text_color="cyan")
            self._show_message(
                f"Push successful   |   Branch: {result.branch}"
                f"   |   Commit: {result.commit_hash}"
                f"   |   Repo: {result.repo_name}",
                "green",
            )
        else:
            self._show_message(f"Push failed: {result.error}", "red")

    def _select_repo(self) -> None:
        dlg = RepoDialog(self)
        self.wait_window(dlg)
        if dlg.selected_path:
            self._repo_label.configure(
                text=git_service.repo_name, text_color="white")
            self._show_message(f"Opened: {dlg.selected_path}", "green")

    def _change_branch(self) -> None:
        if not git_service.is_open:
            self._show_message("Open a repository first.", "orange")
            return
        dlg = BranchDialog(self)
        self.wait_window(dlg)
        if dlg.selected_branch:
            self._branch = dlg.selected_branch
            self._branch_label.configure(
                text=self._branch, text_color="cyan")
            self._status_bar.set_not_synced()

    def _show_history(self) -> None:
        if not git_service.is_open:
            self._show_message("Open a repository first.", "orange")
            return
        HistoryDialog(self)

    def _logout(self) -> None:
        credential_manager.clear()
        self._user_label.configure(text="Not logged in", text_color="gray")
        self._show_message("Logged out. Credentials removed from keyring.", "gray")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _ensure_login(self) -> bool:
        """Return True if valid credentials exist or user logs in successfully."""
        if credential_manager.has_credentials():
            username, _ = credential_manager.load()
            self._user_label.configure(text=username, text_color="green")
            return True
        dlg = LoginDialog(self)
        self.wait_window(dlg)
        if dlg.success:
            username, _ = credential_manager.load()
            self._user_label.configure(text=username, text_color="green")
            return True
        self._show_message("Login required to save to GitHub.", "red")
        return False

    def _stored_username(self) -> str:
        username, _ = credential_manager.load()
        return username if username else "Not logged in"

    def _show_message(self, text: str, color: str = "gray") -> None:
        self._msg_label.configure(text=text, text_color=color)
