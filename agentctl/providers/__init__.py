"""Provider abstractions for agentctl."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str
    name: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Response:
    """A response from an AI provider."""

    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    name: str = "base"

    @abstractmethod
    async def complete(self, messages: list[Message], **kwargs) -> Response:
        """Send messages and get a response."""
        ...

    @abstractmethod
    async def stream(self, messages: list[Message], **kwargs) -> AsyncIterator[str]:
        """Stream response chunks."""
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """List available models for this provider."""
        ...


# Registry of available providers
_providers: dict[str, type[BaseProvider]] = {}


def register_provider(cls: type[BaseProvider]) -> type[BaseProvider]:
    """Register a provider class."""
    _providers[cls.name] = cls
    return cls


def get_provider(name: str) -> type[BaseProvider]:
    """Get a registered provider by name."""
    if name not in _providers:
        available = ", ".join(_providers.keys()) or "none"
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")
    return _providers[name]


def list_providers() -> list[str]:
    """List registered provider names."""
    return list(_providers.keys())
