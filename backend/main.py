from pathlib import Path

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent
# backend/.env (documented) then repo-root .env (common local setup)
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")

import logging
from contextlib import asynccontextmanager

from openai import RateLimitError
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import simulation
from config import settings, validate_settings
from middleware.security import RequestSizeLimitMiddleware, SecurityHeadersMiddleware
from services.llm_json import LLMParseError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_settings()
    yield


app = FastAPI(title="Crowdvise API", lifespan=lifespan)

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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.error("%s %s → %s: %s", request.method, request.url.path, exc.status_code, exc.detail)
    elif exc.status_code >= 400:
        logger.warning("%s %s → %s: %s", request.method, request.url.path, exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(LLMParseError)
async def llm_parse_error_handler(request: Request, exc: LLMParseError):
    logger.error("%s %s → LLM parse error: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(RateLimitError)
async def openai_rate_limit_handler(_request: Request, _exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "AI provider rate limit exceeded. Retry in a minute or use a smaller panel_size."
        },
    )
