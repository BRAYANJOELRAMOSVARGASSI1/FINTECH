"""
main.py — Punto de entrada de la aplicación FastAPI.

Configura middleware, CORS, routers y health check.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_v1_router
from app.config import settings


# ---------------------------------------------------------------------------
# Lifespan — Startup / Shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"[START] FinEngine v{__version__} starting in {settings.app_env} mode...")
    yield
    # Shutdown
    print("[STOP] FinEngine shutting down...")


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------


app = FastAPI(
    title="FinEngine — Motor de Decisión Financiera",
    description=(
        "API para análisis financiero empresarial: conversión de tasas (TEA), "
        "valoración de proyectos (VPN/TIR), tablas de amortización, "
        "análisis CAPEX vs OPEX con escudos fiscales, y simulación "
        "de Monte Carlo para riesgo."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Tasas de Interés",
            "description": "Conversión universal de tasas, Fisher, WACC.",
        },
        {
            "name": "Valoración Financiera",
            "description": "VPN, TIR, FCF, Payback, Índice de Rentabilidad.",
        },
        {
            "name": "Tablas de Amortización",
            "description": "Francés, Alemán, Americano — generación y comparación.",
        },
        {
            "name": "Análisis Financiero",
            "description": "CAPEX vs OPEX, Monte Carlo, análisis de sensibilidad.",
        },
    ],
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Agrega header X-Process-Time a todas las respuestas."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura excepciones no manejadas y devuelve JSON limpio."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": str(exc) if settings.debug else "Error interno del servidor.",
            "status_code": 500,
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# Mount v1 API
app.include_router(api_v1_router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — health check."""
    return {
        "status": "healthy",
        "engine": "FinEngine",
        "version": __version__,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.app_env,
        "debug": settings.debug,
    }
