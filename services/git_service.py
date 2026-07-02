"""
GitService
All Git operations for AutoTest Studio.
Uses GitPython exclusively.  No subprocess calls.
No credentials are ever logged or printed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import git
import requests


@dataclass
class CommitRecord:
    hash: str
    short_hash: str
    message: str
    author: str
    date: str
    branch: str


@dataclass
class PushResult:
    success: bool
    commit_hash: str = ""
    branch: str = ""
    repo_name: str = ""
    error: str = ""


class GitService:
    PROTECTED_BRANCHES = {"main", "master"}

    def __init__(self) -> None:
        self._repo: Optional[git.Repo] = None
        self._repo_path: str = ""

    # ------------------------------------------------------------------ #
    #  Repository                                                          #
    # ------------------------------------------------------------------ #
    def open_repo(self, path: str) -> None:
        """Open an existing local repository."""
        try:
            self._repo = git.Repo(path, search_parent_directories=True)
            self._repo_path = self._repo.working_tree_dir
        except git.InvalidGitRepositoryError:
            raise ValueError(f"No Git repository found at: {path}")

    def clone_repo(self, url: str, local_path: str, username: str, pat: str) -> None:
        """Clone a remote repository using PAT authentication."""
        auth_url = self._inject_credentials(url, username, pat)
        self._repo = git.Repo.clone_from(auth_url, local_path)
        self._repo_path = local_path

    def init_repo(self, path: str) -> None:
        """Initialise a new Git repository at path."""
        self._repo = git.Repo.init(path)
        self._repo_path = path

    @property
    def repo_name(self) -> str:
        if not self._repo:
            return ""
        try:
            return os.path.basename(self._repo_path)
        except Exception:
            return ""

    @property
    def is_open(self) -> bool:
        return self._repo is not None

    # ------------------------------------------------------------------ #
    #  Branches                                                            #
    # ------------------------------------------------------------------ #
    def list_branches(self) -> list[str]:
        self._require_repo()
        return [b.name for b in self._repo.branches]

    def current_branch(self) -> str:
        self._require_repo()
        try:
            return self._repo.active_branch.name
        except TypeError:
            return "HEAD detached"

    def checkout_branch(self, branch_name: str) -> None:
        self._require_repo()
        self._guard_protected(branch_name)
        if branch_name in self.list_branches():
            self._repo.git.checkout(branch_name)
        else:
            self._repo.git.checkout("-b", branch_name)

    def create_branch(self, branch_name: str) -> None:
        self._require_repo()
        self._guard_protected(branch_name)
        if branch_name in self.list_branches():
            raise ValueError(f"Branch '{branch_name}' already exists.")
        self._repo.create_head(branch_name)

    # ------------------------------------------------------------------ #
    #  Stage / Commit / Push                                               #
    # ------------------------------------------------------------------ #
    def stage_all(self) -> None:
        self._require_repo()
        self._repo.git.add(A=True)

    def commit(self, message: str) -> str:
        """Commit staged changes.  Returns the full commit hash."""
        self._require_repo()
        if not self._repo.index.diff("HEAD") and not self._repo.untracked_files:
            # Nothing staged — stage everything
            self.stage_all()
        commit_obj = self._repo.index.commit(message)
        return commit_obj.hexsha

    def push(self, branch: str, username: str, pat: str) -> PushResult:
        """Push branch to origin using PAT.  Never pushes to protected branches."""
        self._require_repo()
        self._guard_protected(branch)
        try:
            origin = self._repo.remotes.origin
            auth_url = self._inject_credentials(origin.url, username, pat)
            with origin.config_writer as cw:
                cw.set("url", auth_url)
            push_info = origin.push(refspec=f"{branch}:{branch}")
            # Restore URL without credentials
            with origin.config_writer as cw:
                cw.set("url", self._strip_credentials(auth_url))
            for info in push_info:
                if info.flags & git.PushInfo.ERROR:
                    return PushResult(success=False, error=str(info.summary))
            head = self._repo.head.commit
            return PushResult(
                success=True,
                commit_hash=head.hexsha[:7],
                branch=branch,
                repo_name=self.repo_name,
            )
        except Exception as exc:
            return PushResult(success=False, error=str(exc))

    def full_workflow(
        self,
        branch: str,
        commit_message: str,
        username: str,
        pat: str,
    ) -> PushResult:
        """
        Complete workflow:
        1. Checkout / create branch
        2. Stage all
        3. Commit
        4. Push
        """
        self._guard_protected(branch)
        self.checkout_branch(branch)
        self.stage_all()
        self.commit(commit_message)
        return self.push(branch, username, pat)

    # ------------------------------------------------------------------ #
    #  History                                                             #
    # ------------------------------------------------------------------ #
    def get_history(self, limit: int = 50) -> list[CommitRecord]:
        self._require_repo()
        records: list[CommitRecord] = []
        try:
            branch = self.current_branch()
            for c in self._repo.iter_commits(branch, max_count=limit):
                records.append(
                    CommitRecord(
                        hash=c.hexsha,
                        short_hash=c.hexsha[:7],
                        message=c.message.strip().splitlines()[0],
                        author=str(c.author),
                        date=c.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                        branch=branch,
                    )
                )
        except Exception:
            pass
        return records

    # ------------------------------------------------------------------ #
    #  Authentication validation                                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def validate_credentials(username: str, pat: str) -> bool:
        """Validate PAT against GitHub API.  Returns True if valid."""
        try:
            resp = requests.get(
                "https://api.github.com/user",
                auth=(username, pat),
                timeout=8,
            )
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def list_remote_repos(username: str, pat: str) -> list[str]:
        """Return list of repo full names the user has access to."""
        try:
            resp = requests.get(
                "https://api.github.com/user/repos",
                auth=(username, pat),
                params={"per_page": 100, "sort": "updated"},
                timeout=8,
            )
            if resp.status_code == 200:
                return [r["full_name"] for r in resp.json()]
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _require_repo(self) -> None:
        if not self._repo:
            raise RuntimeError("No repository is open. Open or clone a repo first.")

    def _guard_protected(self, branch: str) -> None:
        if branch in self.PROTECTED_BRANCHES:
            raise ValueError(
                f"Direct commits to '{branch}' are not allowed. "
                "Create or select a feature branch."
            )

    @staticmethod
    def _inject_credentials(url: str, username: str, pat: str) -> str:
        """Embed credentials into an HTTPS URL without logging them."""
        if url.startswith("https://"):
            return url.replace("https://", f"https://{username}:{pat}@", 1)
        return url

    @staticmethod
    def _strip_credentials(url: str) -> str:
        """Remove embedded credentials from a URL."""
        import re

        return re.sub(r"https://[^@]+@", "https://", url)


git_service = GitService()
