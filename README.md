# agentctl 🤖

A lightweight CLI for managing, monitoring, and debugging AI agents across providers.

Think `kubectl` but for AI agents.

```bash
pip install agentctl
```

## Why?

You're running 5 different agents across OpenAI, Anthropic, and local models. Each has its own API, its own logging format, its own way of doing things. You spend more time switching tabs than building.

`agentctl` gives you one interface to rule them all.

## Features

- **Unified agent management** — Start, stop, monitor agents across providers
- **Real-time streaming logs** — `agentctl logs my-agent --follow`
- **Session management** — Save, restore, and fork agent conversations
- **Cost tracking** — Know exactly what each agent run costs you
- **Local-first** — Everything stored locally. No cloud. No telemetry.
- **Plugin system** — Add your own providers in <50 lines

## Quick Start

```bash
# Configure a provider
agentctl config set openai --api-key sk-...
agentctl config set anthropic --api-key sk-ant-...
agentctl config set ollama --endpoint http://localhost:11434

# List available models
agentctl models

# Start a conversation
agentctl run claude-sonnet "Explain transformers in 3 sentences"

# Start an interactive session
agentctl session new --model gpt-4o --name research-agent

# Stream logs from a running session
agentctl logs research-agent --follow

# Check costs
agentctl costs --today
agentctl costs --this-month --by-model

# Save and restore sessions
agentctl session save research-agent
agentctl session list
agentctl session restore research-agent-2024-02-15

# Fork a conversation (branch from a point)
agentctl session fork research-agent --from-message 5

# Compare model outputs
agentctl compare "What causes inflation?" --models claude-sonnet,gpt-4o,llama3.1
```

## Providers

| Provider | Status | Local? |
|----------|--------|--------|
| OpenAI | ✅ | No |
| Anthropic | ✅ | No |
| Ollama | ✅ | Yes |
| LM Studio | ✅ | Yes |
| Groq | ✅ | No |
| Google Gemini | 🚧 | No |
| Mistral | 🚧 | No |

## Architecture

```
~/.agentctl/
├── config.yaml          # Provider configs & API keys
├── sessions/            # Saved conversation sessions
│   ├── research-agent/
│   │   ├── session.json
│   │   └── messages.jsonl
├── costs/               # Cost tracking data
│   └── 2024-02.json
└── plugins/             # Custom provider plugins
    └── my-provider.py
```

## Plugin System

Add a custom provider in <50 lines:

```python
# ~/.agentctl/plugins/my-provider.py
from agentctl.providers import BaseProvider, Message, Response

class MyProvider(BaseProvider):
    name = "my-llm"
    
    def complete(self, messages: list[Message], **kwargs) -> Response:
        # Your implementation here
        ...
    
    def stream(self, messages: list[Message], **kwargs):
        # Yield chunks for streaming
        ...
    
    def list_models(self) -> list[str]:
        return ["my-model-v1", "my-model-v2"]
```

## Cost Tracking

Every API call is tracked locally. No data leaves your machine.

```bash
$ agentctl costs --this-month --by-model
Model                  Calls    Tokens (in/out)    Cost
─────────────────────────────────────────────────────────
claude-sonnet          142      485K / 89K         $4.21
gpt-4o                 87       312K / 67K         $3.88
llama3.1:8b            203      890K / 156K        $0.00
─────────────────────────────────────────────────────────
Total                  432      1.69M / 312K       $8.09
```

## Configuration

```yaml
# ~/.agentctl/config.yaml
providers:
  openai:
    api_key: sk-...
    default_model: gpt-4o
  anthropic:
    api_key: sk-ant-...
    default_model: claude-sonnet
  ollama:
    endpoint: http://localhost:11434
    default_model: llama3.1:8b

defaults:
  provider: anthropic
  temperature: 0.7
  max_tokens: 4096

costs:
  track: true
  alert_threshold: 50.00  # Alert when monthly spend exceeds this
```

## Development

```bash
git clone https://github.com/anderturing-debug/agentctl.git
cd agentctl
pip install -e ".[dev]"
pytest
```

## Roadmap

- [ ] Agent chaining (pipe output of one agent to another)
- [ ] Scheduled agent runs (cron-like)
- [ ] Web UI dashboard (optional)
- [ ] MCP protocol support
- [ ] Multi-agent orchestration
- [ ] Token budget limits per session

## License

MIT

---

Built by [Ander Turing](https://twitter.com/AnderTurin62549) — because managing AI agents shouldn't require a PhD in YAML.
