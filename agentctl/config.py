"""Configuration management for agentctl."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


AGENTCTL_DIR = Path.home() / ".agentctl"
CONFIG_FILE = AGENTCTL_DIR / "config.yaml"
SESSIONS_DIR = AGENTCTL_DIR / "sessions"
COSTS_DIR = AGENTCTL_DIR / "costs"
PLUGINS_DIR = AGENTCTL_DIR / "plugins"


class ProviderConfig(BaseModel):
    """Configuration for a single provider."""

    api_key: str | None = None
    endpoint: str | None = None
    default_model: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DefaultsConfig(BaseModel):
    """Default settings."""

    provider: str = "anthropic"
    temperature: float = 0.7
    max_tokens: int = 4096


class CostsConfig(BaseModel):
    """Cost tracking settings."""

    track: bool = True
    alert_threshold: float = 50.0


class AgentctlConfig(BaseModel):
    """Root configuration."""

    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    costs: CostsConfig = Field(default_factory=CostsConfig)

    @classmethod
    def load(cls) -> "AgentctlConfig":
        """Load config from disk, or return defaults."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                data = yaml.safe_load(f) or {}
            return cls.model_validate(data)
        return cls()

    def save(self) -> None:
        """Persist config to disk."""
        AGENTCTL_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(self.model_dump(exclude_none=True), f, default_flow_style=False)

    def get_provider(self, name: str | None = None) -> tuple[str, ProviderConfig]:
        """Get a provider config by name, falling back to default."""
        name = name or self.defaults.provider
        if name not in self.providers:
            return name, ProviderConfig()
        return name, self.providers[name]
