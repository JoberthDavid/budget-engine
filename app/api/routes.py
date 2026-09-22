from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.calculate_budget import CalculateBudget
from app.domain.models import (
    BudgetCalculationRequest,
    CompositionItemInput,
    ServiceItemInput,
)


router = APIRouter(
    prefix="/budgets",
    tags=["budgets"],
)


def _decimal(value, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} deve ser numérico.") from exc


def _parse_request(payload: dict) -> BudgetCalculationRequest:
    required = ["project_id", "type_system", "monetary_base_date", "services"]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    services = []
    for raw in payload["services"]:
        compositions = tuple(
            CompositionItemInput(
                composition_id=str(item["composition_id"]),
                reference_base_date=str(item["reference_base_date"]),
                factor=_decimal(item["factor"], "factor"),
            )
            for item in raw.get("compositions", [])
        )
        services.append(
            ServiceItemInput(
                id=str(raw["id"]),
                code=str(raw["code"]),
                description=str(raw["description"]),
                unit=str(raw["unit"]),
                quantity=_decimal(raw["quantity"], "quantity"),
                compositions=compositions,
            )
        )

    return BudgetCalculationRequest(
        project_id=str(payload["project_id"]),
        budget_id=str(payload["budget_id"]) if payload.get("budget_id") is not None else None,
        type_system=str(payload["type_system"]),
        monetary_base_date=str(payload["monetary_base_date"]),
        services=tuple(services),
        overrides=payload.get("overrides") or {},
    )


def _decimal_json(value: Decimal) -> float:
    return float(value)


def _serialize_budget(budget):
    if budget is None:
        return None
    return {
        "id": budget.id,
        "project_id": budget.project_id,
        "type_system": budget.type_system,
        "monetary_base_date": budget.monetary_base_date,
        "total_cost": _decimal_json(budget.total_cost),
        "services": [
            {
                "id": s.id,
                "code": s.code,
                "description": s.description,
                "unit": s.unit,
                "quantity": _decimal_json(s.quantity),
                "unit_cost": _decimal_json(s.unit_cost),
                "total_cost": _decimal_json(s.total_cost),
                "compositions": [
                    {
                        "composition_id": c.composition_id,
                        "reference_base_date": c.reference_base_date,
                        "factor": _decimal_json(c.factor),
                        "unit_cost": _decimal_json(c.unit_cost),
                        "total_cost": _decimal_json(c.total_cost),
                    }
                    for c in s.compositions
                ],
            }
            for s in budget.services
        ],
    }


@router.post("/calculate")
async def calculate(request: Request):
    calculate_budget: CalculateBudget = request.app.state.calculate_budget

    payload = None
    try:
        payload = await request.json()
    except Exception:
        payload = None

    if not isinstance(payload, dict):
        return JSONResponse(
            {"code": "INVALID_JSON", "message": "O corpo deve ser um objeto JSON."},
            status_code=400,
        )
    try:
        calculation_request = _parse_request(payload)
    except (KeyError, TypeError, ValueError) as exc:
        return JSONResponse(
            {"code": "INVALID_REQUEST", "message": str(exc)},
            status_code=400,
        )

    try:
        calculation_id, budget, issues = calculate_budget.execute(calculation_request)
    except NotImplementedError as exc:
        return JSONResponse(
            {"code": "ENGINE_NOT_CONFIGURED", "message": str(exc)},
            status_code=501,
        )

    response = {
        "calculation_id": calculation_id,
        "budget": _serialize_budget(budget),
        "issues": [issue.__dict__ for issue in issues],
        "calculation_metadata": {
            "engine": "composition-engine",
            "engine_version": "unwired",
            "calculated_at": None,
        },
    }
    return JSONResponse(response, status_code=200)
