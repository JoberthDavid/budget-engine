from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.adapters.composition_engine import CompositionEngineAdapter
from app.api.health import router as health_router
from app.api.routes import create_budget_router
from app.application.calculate_budget import CalculateBudget


def create_app(
    calculate_budget: CalculateBudget | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Budget Engine",
        description="Motor de cálculo de orçamentos de engenharia.",
        version="0.1.0",
    )

    if calculate_budget is None:
        composition_engine = CompositionEngineAdapter()
        calculate_budget = CalculateBudget(composition_engine)

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.include_router(health_router)
    app.include_router(
        create_budget_router(calculate_budget)
    )

    return app

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "code": "INVALID_REQUEST",
            "message": "A requisição contém dados inválidos.",
            "details": exc.errors(),
        },
    )