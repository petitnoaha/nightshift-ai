"""
Relance automatique.

Quand un provider IA est indisponible :
  1. l'état courant de la tâche est sauvegardé (voir app/memory/memory_store.py)
  2. le projet passe en WAITING
  3. on attend retry_interval_minutes (60 par défaut)
  4. on revérifie la disponibilité
  5. si dispo -> RECOVERING -> reprise exactement là où on s'était arrêté
     si toujours indispo -> nouvelle attente, jusqu'à max_retries_before_alert
"""
from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.providers.base import ProviderUnavailableError
from app.providers.manager import ProviderManager

logger = logging.getLogger("nightshift.scheduler")


class RetryScheduler:
    def __init__(self, provider_manager: ProviderManager) -> None:
        self.provider_manager = provider_manager
        self.interval_seconds = settings.scheduler.retry_interval_minutes * 60
        self.max_retries = settings.scheduler.max_retries_before_alert

    async def wait_for_provider(self, on_alert=None) -> None:
        """Bloque jusqu'à ce qu'un provider redevienne disponible.
        Ne relance JAMAIS la tâche depuis zéro : c'est à l'appelant de
        conserver l'état (memory_store) avant d'appeler cette fonction."""
        attempts = 0
        while True:
            try:
                await self.provider_manager.get_working_provider()
                logger.info("Provider de nouveau disponible après %s tentative(s).", attempts)
                return
            except ProviderUnavailableError:
                attempts += 1
                logger.warning(
                    "Aucun provider disponible (tentative %s). Nouvelle vérification dans %s min.",
                    attempts, self.interval_seconds // 60,
                )
                if attempts == self.max_retries and on_alert:
                    on_alert(attempts)
                await asyncio.sleep(self.interval_seconds)
