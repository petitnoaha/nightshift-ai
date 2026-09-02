"""
CommandPolicy — filtre toute commande shell qu'un agent veut exécuter.

Trois catégories :
- ALLOWED : exécutée directement (git, python, pytest, npm, ...)
- REQUIRES_VALIDATION : mise en attente, un humain doit valider (rm, sudo, ...)
- BLOCKED : refusée immédiatement (tout ce qui touche des chemins interdits)
"""
from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path

from app.config import settings


@dataclass
class PolicyDecision:
    verdict: str          # "allowed" | "requires_validation" | "blocked"
    reason: str


class CommandPolicy:
    def __init__(self) -> None:
        self.allowlist = set(settings.security.command_allowlist)
        self.validation_required = set(settings.security.require_human_validation_for)
        self.forbidden_paths = [Path(p).resolve() for p in settings.security.forbidden_paths]
        self.workspace_root = Path(settings.security.workspace_root).resolve()

    def evaluate(self, command: str, cwd: str) -> PolicyDecision:
        try:
            parts = shlex.split(command)
        except ValueError as exc:
            return PolicyDecision("blocked", f"Commande illisible : {exc}")

        if not parts:
            return PolicyDecision("blocked", "Commande vide")

        binary = parts[0]

        # 1) Le répertoire de travail doit rester dans le workspace du projet
        cwd_resolved = Path(cwd).resolve()
        if self.workspace_root not in cwd_resolved.parents and cwd_resolved != self.workspace_root:
            return PolicyDecision(
                "blocked",
                f"Répertoire hors workspace autorisé ({self.workspace_root})",
            )

        # 2) Chemins explicitement interdits mentionnés dans la commande
        for forbidden in self.forbidden_paths:
            if str(forbidden) in command:
                return PolicyDecision("blocked", f"Chemin interdit référencé : {forbidden}")

        # 3) Commandes qui exigent une validation humaine
        if binary in self.validation_required:
            return PolicyDecision(
                "requires_validation",
                f"'{binary}' nécessite une validation humaine explicite",
            )

        # 4) Allowlist stricte
        if binary in self.allowlist:
            return PolicyDecision("allowed", "OK")

        return PolicyDecision(
            "blocked",
            f"'{binary}' n'est pas dans l'allowlist ({sorted(self.allowlist)})",
        )
