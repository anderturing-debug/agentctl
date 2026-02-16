"""OpenAI provider — GPT models."""

from __future__ import annotations

import time
from typing import AsyncIterator

import httpx

from agentctl.providers import BaseProvider, Message, Response, register_provider

PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "o1": {"input": 15.0, "output": 60.0},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    for key, prices in PRICING.items():
        if key in model:
            return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    return 0.0


@register_provider
class OpenAIProvider(BaseProvider):
    """Provider for OpenAI models."""

    name = "openai"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com",
            headers={
                "Authorization": f"Bearer {api_key or ''}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    async def complete(self, messages: list[Message], **kwargs) -> Response:
        model = kwargs.get("model", "gpt-4o")
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.7)

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        start = time.monotonic()
        resp = await self.client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        latency = (time.monotonic() - start) * 1000

        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        return Response(
            content=data["choices"][0]["message"]["content"],
            model=model,
            provider="openai",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=_estimate_cost(model, input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model", "gpt-4o")
        max_tokens = kwargs.get("max_tokens", 4096)

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self.client.stream("POST", "/v1/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    import json

                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]

    def list_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini"]
