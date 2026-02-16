"""Ollama provider — local model inference."""

from __future__ import annotations

import time
from typing import AsyncIterator

import httpx

from agentctl.providers import BaseProvider, Message, Response, register_provider


@register_provider
class OllamaProvider(BaseProvider):
    """Provider for local Ollama models."""

    name = "ollama"

    def __init__(self, endpoint: str = "http://localhost:11434", **kwargs):
        self.endpoint = endpoint.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.endpoint, timeout=300.0)

    async def complete(self, messages: list[Message], **kwargs) -> Response:
        model = kwargs.get("model", "llama3.1:8b")
        temperature = kwargs.get("temperature", 0.7)

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }

        start = time.monotonic()
        resp = await self.client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        latency = (time.monotonic() - start) * 1000

        return Response(
            content=data["message"]["content"],
            model=model,
            provider="ollama",
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            cost=0.0,  # Local models are free
            latency_ms=latency,
        )

    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model", "llama3.1:8b")
        temperature = kwargs.get("temperature", 0.7)

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }

        async with self.client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                import json

                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

    def list_models(self) -> list[str]:
        """List models available in Ollama (sync for simplicity)."""
        with httpx.Client(base_url=self.endpoint) as client:
            resp = client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
