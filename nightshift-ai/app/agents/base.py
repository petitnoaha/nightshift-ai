"""Interface commune à tous les agents NightShift."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.providers.base import CompletionResult
from app.providers.manager import ProviderManager


@dataclass
class AgentResult:
    success: bool
    output: str
    provider_result: CompletionResult | None = None
    error: str = ""


class Agent(ABC):
    name: str = "agent"
    status: str = "IDLE"
    current_task: str = ""

    def __init__(self, provider_manager: ProviderManager) -> None:
        self.provider_manager = provider_manager

    @abstractmethod
    def system_prompt(self) -> str:
        """Le rôle de l'agent, injecté comme prompt système."""
        raise NotImplementedError

    async def run(self, task_description: str, context: dict) -> AgentResult:
        """Exécute la tâche. Lève ProviderUnavailableError si aucun provider
        ne répond — l'orchestrateur intercepte et déclenche la relance."""
        self.status = "RUNNING"
        self.current_task = task_description
        provider = await self.provider_manager.get_working_provider()

        user_prompt = self._build_user_prompt(task_description, context)
        result = await provider.complete(self.system_prompt(), user_prompt)

        self.status = "IDLE"
        return AgentResult(success=True, output=result.text, provider_result=result)

    def _build_user_prompt(self, task_description: str, context: dict) -> str:
        ctx_lines = "\n".join(f"- {k}: {v}" for k, v in context.items())
        return (
            f"Tâche : {task_description}\n\n"
            f"Contexte du projet :\n{ctx_lines}\n\n"
            "Réponds de façon concrète et directement exploitable."
        )

    async def resume(self, saved_state: dict) -> None:
        """Reprend un travail interrompu à partir d'un état sauvegardé."""
        self.current_task = saved_state.get("current_task", "")

    async def stop(self) -> None:
        self.status = "STOPPED"
