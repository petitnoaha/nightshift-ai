"""Checkpoints Git automatiques. Utilise le binaire git via subprocess
(pas de dépendance lourde type GitPython, plus simple à déboguer pour un débutant)."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("nightshift.git")


class GitError(Exception):
    pass


class GitManager:
    def __init__(self, workspace: str, branch_prefix: str = "nightshift") -> None:
        self.workspace = Path(workspace)
        self.branch_prefix = branch_prefix

    def _run(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise GitError(f"git {' '.join(args)} a échoué : {result.stderr.strip()}")
        return result.stdout.strip()

    def ensure_repo(self) -> None:
        if not (self.workspace / ".git").exists():
            self._run("init")
            logger.info("Dépôt Git initialisé dans %s", self.workspace)

    def checkpoint(self, task_id: int, label: str) -> str:
        """Crée un commit + une branche de checkpoint. Retourne le hash du commit."""
        self.ensure_repo()
        self._run("add", "-A")
        # Rien à commiter n'est pas une erreur bloquante
        status = self._run("status", "--porcelain")
        if status:
            self._run("commit", "-m", f"[nightshift] task-{task_id}: {label}")
        commit_hash = self._run("rev-parse", "HEAD")
        branch_name = f"{self.branch_prefix}/task-{task_id}-{label}"
        self._run("branch", "-f", branch_name)
        logger.info("Checkpoint créé : %s (%s)", branch_name, commit_hash[:8])
        return commit_hash

    def rollback(self, commit_hash: str) -> None:
        """Revient à un checkpoint précédent SANS supprimer l'historique
        (utilise reset --hard sur une branche de secours, jamais de force-push distant)."""
        safety_branch = f"{self.branch_prefix}/before-rollback-{commit_hash[:8]}"
        self._run("branch", safety_branch)  # filet de sécurité avant le rollback
        self._run("reset", "--hard", commit_hash)
        logger.warning("Rollback effectué vers %s (sauvegarde dans %s)", commit_hash[:8], safety_branch)

    def diff_stats(self, since_commit: str) -> tuple[int, int]:
        """Retourne (lignes ajoutées, lignes supprimées) depuis un commit donné."""
        out = self._run("diff", "--shortstat", since_commit, "HEAD")
        added = removed = 0
        for token in out.split(","):
            token = token.strip()
            if "insertion" in token:
                added = int(token.split()[0])
            elif "deletion" in token:
                removed = int(token.split()[0])
        return added, removed
