"""Provider Anthropic (Claude) — optionnel, désactivé par défaut (paid_enabled: false)."""
from __future__ import annotations

import time

import httpx

from app.providers.base import BaseProvider, CompletionResult, ProviderUnavailableError
from app.security.secrets import get_secret


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, model: str, timeout_seconds: float = 120.0) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(self, system_prompt: str, user_prompt: str) -> CompletionResult:
        api_key = get_secret("anthropic_api_key")
        if not api_key:
            raise ProviderUnavailableError(
                "Aucune clé ANTHROPIC_API_KEY trouvée dans secrets/anthropic_api_key.key"
            )

        start = time.monotonic()
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages", json=payload, headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            raise ProviderUnavailableError(f"Anthropic indisponible : {exc}") from exc

        text = "".join(block.get("text", "") for block in data.get("content", []))
        return CompletionResult(
            text=text, provider=self.name, model=self.model,
            duration_seconds=time.monotonic() - start,
        )

    async def is_available(self) -> bool:
        return get_secret("anthropic_api_key") is not None
