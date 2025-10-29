# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

Claude Code Server is a production-grade FastAPI application that provides HTTP endpoints for Claude AI-powered code execution, analysis, and chat functionality. The server is fully async, includes rate limiting, Prometheus metrics, and comprehensive health checks.

## Architecture

### Core Components

- **server.py**: Single-file FastAPI application containing all endpoints, middleware, and logic
- **Pydantic Settings**: Configuration via environment variables or `.env` file
- **AsyncAnthropic Client**: All Claude API calls use async client for non-blocking operations
- **Middleware Stack**: CORS, rate limiting (slowapi), Prometheus metrics tracking
- **Dependency Injection**: Settings and Claude clients injected via FastAPI's `Depends()`

### Key Patterns

- **Settings Management**: Uses `@lru_cache()` on `get_settings()` for singleton behavior
- **Streaming Support**: All main endpoints (`/execute`, `/chat`, `/analyze`) support both streaming and non-streaming responses via `stream: bool` parameter
- **Metrics Middleware**: Automatically tracks request count, duration, and active requests for all endpoints
- **Error Handling**: All endpoints catch exceptions and return structured error responses with endpoint context
- **Rate Limiting**: Applied per-endpoint via decorator: `@limiter.limit(lambda: get_settings().rate_limit)`

## Development Commands

### Running the Server

```bash
# Local development (requires ANTHROPIC_API_KEY in .env)
python server.py

# Docker
docker-compose up -d

# Systemd (Linux)
sudo systemctl start claude-code-server
```

### Testing

```bash
# Run provided test script (requires server running and ANTHROPIC_API_KEY exported)
./test_server.sh

# Manual endpoint testing
curl http://localhost:8002/health
curl -X POST http://localhost:8002/execute -H "Content-Type: application/json" -d '{"code": "print(2+2)", "language": "python"}'
```

### Code Quality

```bash
# Format code
black server.py

# Lint code
ruff check server.py
```

## Configuration

All configuration via environment variables (see `.env.example`):

- `ANTHROPIC_API_KEY`: Required for Claude API access
- `PORT`: Default 8002
- `RATE_LIMIT`: Format `N/minute` or `N/hour`
- `CLAUDE_MODEL`: Current default is `claude-3-5-sonnet-20241022`
- `MAX_TOKENS`: Max tokens per Claude API request (default 4096)

## Important Implementation Details

### Streaming Responses

When `stream: true`, endpoints return `StreamingResponse` with `media_type="text/plain"`. The async generator pattern is used:

```python
async def stream_response():
    async with client.messages.stream(...) as stream:
        async for text in stream.text_stream:
            yield text
```

### Metrics Collection

Prometheus metrics are incremented in:
- Middleware (all requests): `REQUEST_COUNT`, `REQUEST_DURATION`, `ACTIVE_REQUESTS`
- Endpoint handlers: `CLAUDE_API_CALLS`, `CLAUDE_TOKENS`

Token metrics only tracked for non-streaming responses (usage data unavailable during streaming).

### Request Validation

Pydantic models validate all inputs:
- `CodeRequest`: Validates code length (1-100000), language pattern, prompt length
- `ChatRequest`: Validates message length (1-10000), system prompt length
- Custom validators ensure non-empty stripped content

## API Documentation

When server is running:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## Deployment Options

1. **Docker Compose**: Production-ready with health checks and restart policies
2. **Systemd Service**: Includes security hardening (NoNewPrivileges, PrivateTmp, ProtectSystem)
3. **Direct Python**: Use uvicorn (included in requirements.txt with `[standard]` extra)

## Vibe Chat

**vibe_chat.py** is an interactive terminal UI application that provides a unified natural language interface for both Claude Code Server and GitHub Copilot CLI.

### Architecture

- **Rich TUI**: Uses `rich` library for beautiful terminal UI with markdown rendering, syntax highlighting, and panels
- **Async Design**: Built with `asyncio` for non-blocking AI interactions
- **Dual AI Integration**: 
  - Claude via HTTP client to `localhost:8002/chat` endpoint
  - GitHub Copilot via subprocess calls to `gh copilot suggest`
- **Session Management**: Maintains conversation history and allows switching between AIs mid-conversation

### Key Features

- **AI Switching**: Toggle between Claude and Copilot with `/claude` and `/copilot` commands
- **Markdown Rendering**: Code blocks, formatting, and syntax highlighting in responses
- **Health Checking**: Automatically checks Claude server availability on startup
- **Error Handling**: Graceful degradation when services unavailable

### Commands

```bash
# Run vibe chat directly
python3 vibe_chat.py

# Desktop launcher (installed at ~/.local/share/applications/vibe-chat.desktop)
# Opens in default terminal via x-terminal-emulator
```

### Chat Commands

- `/claude` - Switch to Claude AI
- `/copilot` - Switch to GitHub Copilot
- `/help` - Show command reference
- `/clear` - Clear screen
- `/quit` or `/q` - Exit application

### Dependencies

- `httpx>=0.25.0` - Async HTTP client for Claude API
- `rich>=13.0.0` - Terminal UI and formatting
- `gh` CLI with copilot extension installed

### Implementation Details

**Claude Integration**: Posts to `/chat` endpoint with message and system prompt. Currently uses non-streaming mode (streaming SSE parsing could be added).

**Copilot Integration**: Executes `gh copilot suggest` via subprocess. Note that GitHub Copilot CLI only supports command suggestion, not full conversational chat.

**UI Pattern**: Uses Rich's `Console.status()` for loading indicators and `Markdown()` renderer for AI responses. Conversation history stored in memory (not persisted).

### Code Quality

```bash
# Format
black vibe_chat.py

# Lint
ruff check vibe_chat.py
```
