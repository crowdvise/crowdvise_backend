from contextlib import asynccontextmanager

from dotenv import load_dotenv
from anthropic import RateLimitError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import simulation
from config import settings, validate_settings
from middleware.security import RequestSizeLimitMiddleware, SecurityHeadersMiddleware
from services.llm_json import LLMParseError

load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_settings()
    yield


app = FastAPI(title="CrowdVise API", lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(simulation.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(LLMParseError)
async def llm_parse_error_handler(_request: Request, exc: LLMParseError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(RateLimitError)
async def anthropic_rate_limit_handler(_request: Request, _exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "AI provider rate limit exceeded. Retry in a minute or use a smaller panel_size."
        },
    )
