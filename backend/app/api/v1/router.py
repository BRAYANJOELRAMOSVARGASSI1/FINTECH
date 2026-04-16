"""
api/v1/router.py — Router principal que agrupa todos los sub-routers.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.amortization import router as amortization_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.rates import router as rates_router
from app.api.v1.valuation import router as valuation_router
from app.api.v1.export import router as export_router
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.startup_routes import router as startup_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(rates_router)
api_v1_router.include_router(valuation_router)
api_v1_router.include_router(amortization_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(export_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(startup_router)
