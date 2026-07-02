"""
CredentialManager
Stores GitHub credentials exclusively in the OS keyring (Windows Credential
Manager / macOS Keychain / Linux Secret Service).  The PAT is never written
to any file or logged.
"""

from __future__ import annotations

import keyring

_SERVICE = "AutoTestStudio_GitHub"
_USERNAME_KEY = "github_username"


class CredentialManager:
    # ------------------------------------------------------------------ #
    #  Store / retrieve                                                    #
    # ------------------------------------------------------------------ #
    def save(self, username: str, pat: str) -> None:
        """Persist username + PAT in the OS keyring."""
        keyring.set_password(_SERVICE, _USERNAME_KEY, username)
        keyring.set_password(_SERVICE, username, pat)

    def load(self) -> tuple[str, str] | tuple[None, None]:
        """Return (username, PAT) or (None, None) if not stored."""
        username = keyring.get_password(_SERVICE, _USERNAME_KEY)
        if not username:
            return None, None
        pat = keyring.get_password(_SERVICE, username)
        return username, pat

    def clear(self) -> None:
        """Remove all stored credentials."""
        username = keyring.get_password(_SERVICE, _USERNAME_KEY)
        if username:
            keyring.delete_password(_SERVICE, username)
        try:
            keyring.delete_password(_SERVICE, _USERNAME_KEY)
        except Exception:
            pass

    def has_credentials(self) -> bool:
        username, pat = self.load()
        return bool(username and pat)


credential_manager = CredentialManager()
