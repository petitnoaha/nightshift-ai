"""Provider Ollama — 100% local, gratuit, ne jamais exposer 11434 à Internet."""
from __future__ import annotations

import time

import httpx

from app.providers.base import BaseProvider, CompletionResult, ProviderUnavailableError


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(self, system_prompt: str, user_prompt: str) -> CompletionResult:
        start = time.monotonic()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            raise ProviderUnavailableError(f"Ollama indisponible : {exc}") from exc

        text = data.get("message", {}).get("content", "")
        return CompletionResult(
            text=text,
            provider=self.name,
            model=self.model,
            duration_seconds=time.monotonic() - start,
        )

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
