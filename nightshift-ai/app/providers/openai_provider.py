"""Provider OpenAI — optionnel, désactivé par défaut (paid_enabled: false)."""
from __future__ import annotations

import time

import httpx

from app.providers.base import BaseProvider, CompletionResult, ProviderUnavailableError
from app.security.secrets import get_secret


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, model: str, timeout_seconds: float = 120.0) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def complete(self, system_prompt: str, user_prompt: str) -> CompletionResult:
        api_key = get_secret("openai_api_key")
        if not api_key:
            raise ProviderUnavailableError(
                "Aucune clé OPENAI_API_KEY trouvée dans secrets/openai_api_key.key"
            )

        start = time.monotonic()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            raise ProviderUnavailableError(f"OpenAI indisponible : {exc}") from exc

        text = data["choices"][0]["message"]["content"]
        return CompletionResult(
            text=text, provider=self.name, model=self.model,
            duration_seconds=time.monotonic() - start,
        )

    async def is_available(self) -> bool:
        return get_secret("openai_api_key") is not None
