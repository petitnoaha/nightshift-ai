"""Interface commune à tous les fournisseurs IA (Ollama, OpenAI, Anthropic, ...)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderUnavailableError(Exception):
    """Levée quand le provider ne répond pas (quota épuisé, réseau, timeout...).
    L'orchestrateur intercepte cette erreur pour déclencher la relance automatique."""


@dataclass
class CompletionResult:
    text: str
    provider: str
    model: str
    duration_seconds: float


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> CompletionResult:
        """Envoie un prompt et retourne la réponse. Lève ProviderUnavailableError en cas d'échec."""
        raise NotImplementedError

    @abstractmethod
    async def is_available(self) -> bool:
        """Vérification rapide de santé (utilisée par le healthcheck)."""
        raise NotImplementedError
