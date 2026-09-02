"""
Sélectionne le provider IA à utiliser, dans l'ordre de priorité configuré.

Règle : Ollama d'abord (gratuit, local). Un provider payant n'est JAMAIS
utilisé tant que enabled=true ET paid_enabled=true ne sont pas les deux
réglés explicitement dans config.yaml (ou config.local.yaml).
"""
from __future__ import annotations

import logging

from app.config import settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseProvider, ProviderUnavailableError
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger("nightshift.providers")


class ProviderManager:
    def __init__(self) -> None:
        self._providers: list[BaseProvider] = []
        self._build()

    def _build(self) -> None:
        entries = []
        for provider_name, cfg in settings.providers.items():
            if not cfg.enabled:
                continue
            if provider_name != "ollama" and not cfg.paid_enabled:
                logger.info(
                    "Provider '%s' activé mais paid_enabled=false : ignoré (gratuit uniquement).",
                    provider_name,
                )
                continue

            if provider_name == "ollama":
                entries.append((cfg.priority, OllamaProvider(cfg.base_url or "http://127.0.0.1:11434", cfg.model)))
            elif provider_name == "openai":
                entries.append((cfg.priority, OpenAIProvider(cfg.model)))
            elif provider_name == "anthropic":
                entries.append((cfg.priority, AnthropicProvider(cfg.model)))

        entries.sort(key=lambda pair: pair[0])
        self._providers = [p for _, p in entries]

        if not self._providers:
            logger.warning(
                "Aucun provider actif ! Vérifie config.yaml (ollama.enabled devrait être true)."
            )

    async def get_working_provider(self) -> BaseProvider:
        """Retourne le premier provider disponible dans l'ordre de priorité.
        Lève ProviderUnavailableError si aucun ne répond (déclenche la relance
        automatique côté scheduler)."""
        for provider in self._providers:
            if await provider.is_available():
                return provider
        raise ProviderUnavailableError(
            "Aucun provider IA disponible actuellement (Ollama down ? clés absentes ?)"
        )
