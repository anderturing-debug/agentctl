"""Anthropic provider — Claude models."""

from __future__ import annotations

import time
from typing import AsyncIterator

import httpx

from agentctl.providers import BaseProvider, Message, Response, register_provider

# Pricing per 1M tokens (as of Feb 2026)
PRICING = {
    "claude-sonnet": {"input": 3.0, "output": 15.0},
    "claude-haiku": {"input": 0.25, "output": 1.25},
    "claude-opus": {"input": 15.0, "output": 75.0},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost based on token usage."""
    for key, prices in PRICING.items():
        if key in model:
            return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
    return 0.0


@register_provider
class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key or "",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=120.0,
        )

    async def complete(self, messages: list[Message], **kwargs) -> Response:
        model = kwargs.get("model", "claude-sonnet-4-20250514")
        max_tokens = kwargs.get("max_tokens", 4096)
        temperature = kwargs.get("temperature", 0.7)

        # Extract system message if present
        system = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }
        if system:
            payload["system"] = system

        start = time.monotonic()
        resp = await self.client.post("/v1/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()
        latency = (time.monotonic() - start) * 1000

        input_tokens = data.get("usage", {}).get("input_tokens", 0)
        output_tokens = data.get("usage", {}).get("output_tokens", 0)

        return Response(
            content=data["content"][0]["text"],
            model=model,
            provider="anthropic",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=_estimate_cost(model, input_tokens, output_tokens),
            latency_ms=latency,
        )

    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[str]:
        model = kwargs.get("model", "claude-sonnet-4-20250514")
        max_tokens = kwargs.get("max_tokens", 4096)

        system = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": chat_messages,
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with self.client.stream("POST", "/v1/messages", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    import json

                    event = json.loads(line[6:])
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if "text" in delta:
                            yield delta["text"]

    def list_models(self) -> list[str]:
        return [
            "claude-sonnet-4-20250514",
            "claude-haiku-3-5-20241022",
            "claude-opus-4-20250514",
        ]
