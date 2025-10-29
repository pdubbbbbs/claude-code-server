# Claude Code Server 🚀

Production-grade FastAPI server powered by Claude AI for code execution, analysis, and chat.

## ✨ Features

### Claude Code Server
- **Code Execution**: Execute code in multiple languages via Claude AI
- **Code Analysis**: Get security, performance, and best practices feedback
- **AI Chat**: Interactive chat with Claude for coding questions
- **Streaming Support**: Real-time streaming responses for all endpoints
- **Rate Limiting**: Built-in protection with configurable limits
- **Prometheus Metrics**: Monitor API usage and performance
- **Health Checks**: Comprehensive health monitoring
- **Input Validation**: Robust request validation with Pydantic
- **Async/Await**: Fully async for maximum performance
- **Production Ready**: Docker, systemd, and logging included

### 🎵 Vibe Chat
- **Dual AI Interface**: Chat with both Claude and GitHub Copilot in one terminal app
- **Beautiful TUI**: Rich terminal UI with markdown rendering and syntax highlighting
- **AI Switching**: Toggle between Claude and Copilot with simple commands
- **Desktop Integration**: Launch from applications menu with one click
- **Natural Language**: Ask coding questions in plain English
- **Command Helper**: Built-in help and command reference

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Run the server:**
```bash
python server.py
```

Server runs on: http://localhost:8002

### Vibe Chat 🎵

1. **Install dependencies:**
```bash
pip install httpx rich
```

2. **Ensure prerequisites:**
- Claude Code Server running on `localhost:8002`
- GitHub Copilot CLI installed: `gh extension install github/gh-copilot`

3. **Run Vibe Chat:**
```bash
python3 vibe_chat.py
```

4. **Or launch from desktop:**
```bash
# Install desktop launcher
cp vibe-chat.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
# Then find "Vibe Chat" in your applications menu
```

**Commands:**
- `/claude` - Switch to Claude AI
- `/copilot` - Switch to GitHub Copilot  
- `/help` - Show help
- `/clear` - Clear screen
- `/quit` - Exit

### Docker

```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t claude-code-server .
docker run -p 8002:8002 -e ANTHROPIC_API_KEY=your-key claude-code-server
```

### Systemd Service (Linux)

```bash
# Copy service file
sudo cp claude-code-server.service /etc/systemd/system/

# Edit and add your API key
sudo nano /etc/systemd/system/claude-code-server.service

# Enable and start
sudo systemctl enable claude-code-server
sudo systemctl start claude-code-server
sudo systemctl status claude-code-server
```

## 📡 API Endpoints

### Health & Monitoring

#### `GET /`
Basic health check

#### `GET /health`
Comprehensive health check with Claude API connectivity test

#### `GET /metrics`
Prometheus metrics endpoint

### Core Endpoints

#### `POST /execute`
Execute code using Claude AI

**Request:**
```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(2+2)",
    "language": "python",
    "stream": false
  }'
```

**Streaming:**
```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "for i in range(5): print(i)",
    "language": "python",
    "stream": true
  }' --no-buffer
```

#### `POST /chat`
Chat with Claude about code

**Request:**
```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain async/await in Python",
    "system_prompt": "You are a Python expert",
    "stream": false
  }'
```

#### `POST /analyze`
Analyze code for bugs, security, and improvements

**Request:**
```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a,b): return a+b",
    "language": "python",
    "stream": false
  }'
```

## ⚙️ Configuration

Configure via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *required* | Your Claude API key |
| `ENVIRONMENT` | `development` | Environment mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8002` | Server port |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `RATE_LIMIT` | `100/minute` | Rate limit per IP |
| `CLAUDE_MODEL` | `claude-3-5-sonnet-20241022` | Claude model to use |
| `MAX_TOKENS` | `4096` | Max tokens per request |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |

## 📊 Monitoring

### Prometheus Metrics

Access metrics at `http://localhost:8002/metrics`

**Available metrics:**
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_active` - Currently active requests
- `claude_api_calls_total` - Total Claude API calls by endpoint and status
- `claude_tokens_total` - Total tokens used (input/output)

### Logs

Structured logging with timestamps, levels, and context:
```
2025-10-28 19:34:51 - server - INFO - 🚀 Starting Claude Code Server
2025-10-28 19:34:51 - server - INFO - Environment: production
2025-10-28 19:34:51 - server - INFO - Model: claude-3-5-sonnet-20241022
```

## 🔒 Security

- **Rate Limiting**: Prevents abuse with configurable limits
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Detailed error responses without leaking internals
- **CORS**: Configurable CORS policies
- **Non-root User**: Docker runs as non-root user
- **Systemd Hardening**: Security features in service file

## 🛠️ Development

### Install dev dependencies:
```bash
pip install -r requirements.txt
```

### Run tests:
```bash
pytest tests/
```

### Code formatting:
```bash
black server.py
ruff check server.py
```

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - feel free to use in your projects!

## 🆘 Troubleshooting

### Server won't start
- Check `ANTHROPIC_API_KEY` is set correctly
- Verify port 8002 is not in use: `lsof -i :8002`
- Check logs for detailed error messages

### Health check fails
- Verify Claude API key is valid
- Check internet connectivity
- Review `/health` endpoint response for details

### Rate limit errors
- Adjust `RATE_LIMIT` in environment variables
- Consider implementing API key-based rate limiting

## 🚀 Performance Tips

1. **Use streaming** for long responses to reduce perceived latency
2. **Configure rate limits** based on your Claude API tier
3. **Monitor metrics** to identify bottlenecks
4. **Use async clients** when making multiple requests
5. **Scale horizontally** with Docker/Kubernetes for high traffic

---

Built with ❤️ using FastAPI and Claude AI
