# Scenario 6 – Microsoft Agent Framework + Local LLM (TinyLlama via Docker)

This scenario demonstrates building a **multi-turn console chat agent** in .NET using the
[Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/) while
delegating response generation to a locally-running LLM served by
[Ollama](https://ollama.com/) inside Docker.

By default the scenario uses **TinyLlama** (a lightweight 1.1B-parameter model that runs
on CPU), but any model available in the Ollama library can be swapped in via a single
environment variable.

---

## Architecture

```
┌─────────────────────────────────────┐
│  .NET Console App (AgentChat)       │
│                                     │
│  Program.cs                         │
│    └─ DI container                  │
│         └─ LocalLlmAgent            │
│              ├─ LlmClientFactory    │
│              │    └─ OpenAI.ChatClient (pointing at Ollama)
│              └─ Microsoft.Agents.AI │
│                   .AIAgent          │
│                   .AgentSession ◄───┼──── multi-turn history
└────────────────┬────────────────────┘
                 │ HTTP (OpenAI-compatible /v1/chat/completions)
                 ▼
┌─────────────────────────────────────┐
│  Ollama container (Docker)          │
│  – serves any model via             │
│    OpenAI-compatible REST API       │
│  Default model: tinyllama           │
└─────────────────────────────────────┘
```

### Key components

| File | Purpose |
|------|---------|
| `AgentChat/Program.cs` | DI setup, configuration loading, interactive console loop |
| `AgentChat/Agent/LocalLlmAgent.cs` | Wraps `AIAgent` (Microsoft Agent Framework); exposes `ChatAsync` for multi-turn chat |
| `AgentChat/Services/LlmClientFactory.cs` | Builds an `OpenAI.Chat.ChatClient` targeting the local endpoint |
| `AgentChat/Services/LlmOptions.cs` | Strongly-typed configuration class |
| `AgentChat.Tests/LlmClientFactoryTests.cs` | Unit tests for the factory (no LLM required) |
| `docker-compose.yml` | Starts Ollama + (optionally) the .NET app |
| `Dockerfile` | Multi-stage Docker build for the .NET app |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [.NET 10 SDK](https://dotnet.microsoft.com/download) | Required to build/run without Docker |
| [Docker Desktop](https://docs.docker.com/get-docker/) | Required to run Ollama |
| NVIDIA GPU (optional) | Speeds up inference; CPU mode works for TinyLlama |
| NVIDIA Container Toolkit (optional) | Only needed for GPU passthrough in Docker |

---

## Quickstart (recommended)

### 1. Start Ollama

```bash
docker compose up ollama -d
```

### 2. Pull TinyLlama

```bash
docker compose --profile init run --rm ollama-init
# Or manually: docker exec scenario6-ollama ollama pull tinyllama
```

### 3a. Run the chat app locally (no Docker for the .NET app)

```bash
cd AgentChat
dotnet run
```

### 3b. Or run everything in Docker

```bash
docker compose up agentchat
```

---

## Configuration

All settings can be overridden via **environment variables** (short form) or via
`AgentChat/appsettings.json` (Options pattern, section `Llm`).

| Environment variable | `appsettings.json` key | Default | Description |
|---------------------|------------------------|---------|-------------|
| `LLM_ENDPOINT_URL` | `Llm:EndpointUrl` | `http://localhost:11434/v1/` | Base URL of the OpenAI-compatible endpoint |
| `MODEL_NAME` | `Llm:ModelName` | `tinyllama` | Model name sent with every request |
| `LLM_API_KEY` | `Llm:ApiKey` | `not-required` | API key (Ollama ignores it; keep for compatibility) |
| *(no short form)* | `Llm:SystemPrompt` | *"You are a helpful AI assistant…"* | Agent system instruction |
| `Logging__LogLevel__Default` | `Logging:LogLevel:Default` | `Warning` | .NET log level |

### Switching models

Any model in the [Ollama library](https://ollama.com/library) can be used:

```bash
# Pull the model first
docker exec scenario6-ollama ollama pull phi4-mini

# Then start the app with MODEL_NAME overridden
MODEL_NAME=phi4-mini dotnet run --project AgentChat
# or in docker-compose
MODEL_NAME=phi4-mini docker compose up agentchat
```

---

## Build & Test

```bash
# Restore, build, test (no LLM required)
cd scenario6
dotnet restore
dotnet build
dotnet test
```

Expected output:
```
Passed!  - Failed: 0, Passed: 4, Skipped: 0
```

---

## Running end-to-end

```
╔══════════════════════════════════════════════════════╗
║   Scenario 6 – Microsoft Agent Framework Chat        ║
╚══════════════════════════════════════════════════════╝
  Endpoint : http://localhost:11434/v1/
  Model    : tinyllama

Type your message and press Enter. Type 'exit' to quit.

You: Hello! Who are you?
Assistant: Hi there! I'm an AI assistant powered by TinyLlama running locally
on your machine. How can I help you today?

You: What did I just ask you?
Assistant: You asked me to introduce myself. You said: "Hello! Who are you?"

You: exit
Goodbye!
```

---

## How Microsoft Agent Framework is used

The scenario uses three key Agent Framework APIs:

```csharp
// 1. Create an AIAgent from any OpenAI-compatible ChatClient
AIAgent agent = chatClient.AsAIAgent(instructions: "...", name: "LocalAssistant");

// 2. Start a multi-turn conversation session (preserves history automatically)
AgentSession session = await agent.CreateSessionAsync();

// 3. Send messages – context is retained across turns
var response = await agent.RunAsync("Hello!", session);
Console.WriteLine(response.Text);
```

The `AgentSession` object carries conversation history; passing it to every
`RunAsync` call enables the agent to reference previous exchanges.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection refused` on port 11434 | Start Ollama: `docker compose up ollama -d` |
| Model not found | Pull the model first: `docker exec scenario6-ollama ollama pull tinyllama` |
| Slow responses | Normal for CPU mode with larger models; use TinyLlama or add a GPU |
| GPU not detected | Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) and add `--gpus=all` |
| `NU1605` on restore | Pin the conflicting package to the version that the Agent Framework requires |

---

## Related resources

- [Microsoft Agent Framework docs](https://learn.microsoft.com/en-us/agent-framework/)
- [Microsoft.Agents.AI NuGet package](https://www.nuget.org/packages/Microsoft.Agents.AI)
- [Ollama model library](https://ollama.com/library)
- [OpenAI-compatible Ollama API](https://ollama.com/blog/openai-compatibility)
