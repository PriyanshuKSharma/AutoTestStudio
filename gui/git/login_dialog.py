"""
GitHub Login Dialog
Shown only when no valid credentials are stored in keyring.
PAT is never written to any file.
"""
from __future__ import annotations

import customtkinter as ctk
from services.credential_manager import credential_manager
from services.git_service import git_service


class LoginDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("GitHub Login")
        self.geometry("420x340")
        self.resizable(False, False)
        self.grab_set()

        self.success = False
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="GitHub Authentication",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(24, 4))
        ctk.CTkLabel(self, text="Enter your GitHub username and Personal Access Token.",
                     text_color="gray").pack(pady=(0, 16))

        form = ctk.CTkFrame(self)
        form.pack(padx=32, fill="x")

        ctk.CTkLabel(form, text="Username", anchor="w").grid(
            row=0, column=0, padx=8, pady=8, sticky="w")
        self._username = ctk.CTkEntry(form, width=240, placeholder_text="github-username")
        self._username.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(form, text="Access Token", anchor="w").grid(
            row=1, column=0, padx=8, pady=8, sticky="w")
        self._pat = ctk.CTkEntry(form, width=240, show="*",
                                 placeholder_text="ghp_xxxxxxxxxxxx")
        self._pat.grid(row=1, column=1, padx=8, pady=8)

        self._remember = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Remember login (stored securely in OS keyring)",
                        variable=self._remember).pack(pady=8)

        self._status = ctk.CTkLabel(self, text="", text_color="red")
        self._status.pack()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=12)
        ctk.CTkButton(btn_row, text="Cancel", width=100, fg_color="gray40",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Login", width=100,
                      command=self._login).pack(side="left", padx=8)

        # Pre-fill stored username if available
        stored_user, _ = credential_manager.load()
        if stored_user:
            self._username.insert(0, stored_user)

    def _login(self) -> None:
        username = self._username.get().strip()
        pat = self._pat.get().strip()

        if not username or not pat:
            self._status.configure(text="Username and token are required.")
            return

        self._status.configure(text="Validating...", text_color="gray")
        self.update()

        if not git_service.validate_credentials(username, pat):
            self._status.configure(
                text="Authentication failed. Check username and token.", text_color="red")
            return

        if self._remember.get():
            credential_manager.save(username, pat)

        self.success = True
        self.destroy()
