from fastapi import FastAPI

from app.adapters.composition_engine import CompositionEngineAdapter
from app.api.health import router as health_router
from app.api.routes import router as budget_router
from app.application.calculate_budget import CalculateBudget


def create_app() -> FastAPI:
    app = FastAPI(
        title="Budget Engine",
        description="Motor de cálculo de orçamentos de engenharia.",
        version="0.1.0",
    )

    composition_engine = CompositionEngineAdapter()
    calculate_budget = CalculateBudget(composition_engine)

    app.state.calculate_budget = calculate_budget

    app.include_router(health_router)
    app.include_router(budget_router)

    return app