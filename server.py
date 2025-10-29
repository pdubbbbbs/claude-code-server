"""Claude Code Execution Server - Execute code via Claude API."""

import os
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from anthropic import Anthropic, AsyncAnthropic
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('http_requests_active', 'Active HTTP requests')
CLAUDE_API_CALLS = Counter('claude_api_calls_total', 'Total Claude API calls', ['endpoint', 'status'])
CLAUDE_TOKENS = Counter('claude_tokens_total', 'Total Claude tokens used', ['type'])


class Settings(BaseSettings):
    """Application settings with validation."""
    anthropic_api_key: str
    environment: str = 'development'
    host: str = '0.0.0.0'
    port: int = 8002
    cors_origins: str = '*'
    rate_limit: str = '100/minute'
    max_tokens: int = 4096
    claude_model: str = 'claude-3-5-sonnet-20241022'
    enable_metrics: bool = True
    
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=False,
        extra='ignore'
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management."""
    logger.info("🚀 Starting Claude Code Server")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Model: {settings.claude_model}")
    yield
    logger.info("👋 Shutting down Claude Code Server")


app = FastAPI(
    title="Claude Code Server",
    description="Production-grade code execution using Claude AI",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics."""
    ACTIVE_REQUESTS.inc()
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    finally:
        ACTIVE_REQUESTS.dec()


# Initialize Claude clients
def get_claude_client(settings: Settings = Depends(get_settings)) -> Anthropic:
    """Get synchronous Claude client."""
    return Anthropic(api_key=settings.anthropic_api_key)


def get_async_claude_client(settings: Settings = Depends(get_settings)) -> AsyncAnthropic:
    """Get async Claude client."""
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


# Request models with validation
class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000)
    language: str = Field(default="python", pattern="^[a-zA-Z+#]+$")
    prompt: Optional[str] = Field(None, max_length=10000)
    stream: bool = Field(default=False)
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    system_prompt: Optional[str] = Field(None, max_length=10000)
    stream: bool = Field(default=False)
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Claude Code Server",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.environment,
        "model": settings.claude_model
    }
    
    # Test Claude API connectivity
    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        # Quick test with minimal tokens
        client.messages.create(
            model=settings.claude_model,
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
        health_status["claude_api"] = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["claude_api"] = "disconnected"
        health_status["error"] = str(e)
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@app.get("/metrics")
async def metrics(settings: Settings = Depends(get_settings)):
    """Prometheus metrics endpoint."""
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return StreamingResponse(
        prometheus_client.generate_latest(),
        media_type="text/plain"
    )


# Main endpoints
@app.post("/execute")
@limiter.limit(lambda: get_settings().rate_limit)
async def execute_code(
    request: Request,
    code_request: CodeRequest,
    settings: Settings = Depends(get_settings)
):
    """Execute code using Claude with streaming support."""
    try:
        prompt = code_request.prompt or f"Execute this {code_request.language} code and return the result:\n\n```{code_request.language}\n{code_request.code}\n```"
        
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        if code_request.stream:
            async def stream_response():
                try:
                    async with client.messages.stream(
                        model=settings.claude_model,
                        max_tokens=settings.max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        async for text in stream.text_stream:
                            yield text
                    
                    CLAUDE_API_CALLS.labels(endpoint='execute', status='success').inc()
                except Exception as e:
                    CLAUDE_API_CALLS.labels(endpoint='execute', status='error').inc()
                    logger.error(f"Streaming error: {e}")
                    yield f"\n\nError: {str(e)}"
            
            return StreamingResponse(stream_response(), media_type="text/plain")
        
        else:
            message = await client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            CLAUDE_API_CALLS.labels(endpoint='execute', status='success').inc()
            CLAUDE_TOKENS.labels(type='input').inc(message.usage.input_tokens)
            CLAUDE_TOKENS.labels(type='output').inc(message.usage.output_tokens)
            
            return {
                "status": "success",
                "result": message.content[0].text,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                },
                "model": settings.claude_model
            }
            
    except Exception as e:
        CLAUDE_API_CALLS.labels(endpoint='execute', status='error').inc()
        logger.error(f"Execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "endpoint": "execute"
        })


@app.post("/chat")
@limiter.limit(lambda: get_settings().rate_limit)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    settings: Settings = Depends(get_settings)
):
    """Chat with Claude with streaming support."""
    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        kwargs = {
            "model": settings.claude_model,
            "max_tokens": settings.max_tokens,
            "messages": [{"role": "user", "content": chat_request.message}]
        }
        
        if chat_request.system_prompt:
            kwargs["system"] = chat_request.system_prompt
        
        if chat_request.stream:
            async def stream_response():
                try:
                    async with client.messages.stream(**kwargs) as stream:
                        async for text in stream.text_stream:
                            yield text
                    
                    CLAUDE_API_CALLS.labels(endpoint='chat', status='success').inc()
                except Exception as e:
                    CLAUDE_API_CALLS.labels(endpoint='chat', status='error').inc()
                    logger.error(f"Streaming error: {e}")
                    yield f"\n\nError: {str(e)}"
            
            return StreamingResponse(stream_response(), media_type="text/plain")
        
        else:
            message = await client.messages.create(**kwargs)
            
            CLAUDE_API_CALLS.labels(endpoint='chat', status='success').inc()
            CLAUDE_TOKENS.labels(type='input').inc(message.usage.input_tokens)
            CLAUDE_TOKENS.labels(type='output').inc(message.usage.output_tokens)
            
            return {
                "status": "success",
                "response": message.content[0].text,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                },
                "model": settings.claude_model
            }
            
    except Exception as e:
        CLAUDE_API_CALLS.labels(endpoint='chat', status='error').inc()
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "endpoint": "chat"
        })


@app.post("/analyze")
@limiter.limit(lambda: get_settings().rate_limit)
async def analyze_code(
    request: Request,
    code_request: CodeRequest,
    settings: Settings = Depends(get_settings)
):
    """Analyze code using Claude."""
    try:
        prompt = f"Analyze this {code_request.language} code for bugs, security issues, performance improvements, and best practices:\n\n```{code_request.language}\n{code_request.code}\n```\n\nProvide specific, actionable feedback."
        
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        if code_request.stream:
            async def stream_response():
                try:
                    async with client.messages.stream(
                        model=settings.claude_model,
                        max_tokens=settings.max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        async for text in stream.text_stream:
                            yield text
                    
                    CLAUDE_API_CALLS.labels(endpoint='analyze', status='success').inc()
                except Exception as e:
                    CLAUDE_API_CALLS.labels(endpoint='analyze', status='error').inc()
                    logger.error(f"Streaming error: {e}")
                    yield f"\n\nError: {str(e)}"
            
            return StreamingResponse(stream_response(), media_type="text/plain")
        
        else:
            message = await client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            CLAUDE_API_CALLS.labels(endpoint='analyze', status='success').inc()
            CLAUDE_TOKENS.labels(type='input').inc(message.usage.input_tokens)
            CLAUDE_TOKENS.labels(type='output').inc(message.usage.output_tokens)
            
            return {
                "status": "success",
                "analysis": message.content[0].text,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                },
                "model": settings.claude_model
            }
            
    except Exception as e:
        CLAUDE_API_CALLS.labels(endpoint='analyze', status='error').inc()
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "endpoint": "analyze"
        })


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=True
    )
