from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.mappers import map_budget_calculation_request
from app.api.schemas import (
    BudgetCalculationRequestSchema,
    BudgetCalculationResponse,
    CalculatedBudgetResponse,
    CompositionResultResponse,
    ServiceItemResultResponse,
    ValidationIssueResponse,
)
from app.application.calculate_budget import CalculateBudget


def create_budget_router(
    calculate_budget: CalculateBudget,
) -> APIRouter:
    router = APIRouter(
        prefix="/budgets",
        tags=["budgets"],
    )

    def get_calculate_budget() -> CalculateBudget:
        return calculate_budget

    @router.post(
        "/calculate",
        response_model=BudgetCalculationResponse,
    )
    def calculate(
        request: BudgetCalculationRequestSchema,
        calculate_budget: CalculateBudget = Depends(
            get_calculate_budget
        ),
    ) -> BudgetCalculationResponse:
        calculation_request = map_budget_calculation_request(request)

        calculation_id, budget, issues = calculate_budget.execute(
            calculation_request
        )

        return _to_response(
            calculation_id=calculation_id,
            budget=budget,
            issues=issues,
        )

    return router


def _to_response(
    calculation_id: str,
    budget,
    issues,
) -> BudgetCalculationResponse:
    budget_response = None

    if budget is not None:
        budget_response = CalculatedBudgetResponse(
            id=budget.id,
            project_id=budget.project_id,
            methodology=budget.methodology,
            type_system=budget.type_system,
            monetary_base_date=budget.monetary_base_date,
            total_cost=budget.total_cost,
            services=[
                ServiceItemResultResponse(
                    id=service.id,
                    code=service.code,
                    description=service.description,
                    unit=service.unit,
                    quantity=service.quantity,
                    unit_cost=service.unit_cost,
                    total_cost=service.total_cost,
                    compositions=[
                        CompositionResultResponse(
                            composition_id=composition.composition_id,
                            reference_base_date=composition.reference_base_date,
                            factor=composition.factor,
                            unit_cost=composition.unit_cost,
                            total_cost=composition.total_cost,
                        )
                        for composition in service.compositions
                    ],
                )
                for service in budget.services
            ],
        )

    return BudgetCalculationResponse(
        calculation_id=calculation_id,
        budget=budget_response,
        issues=[
            ValidationIssueResponse(
                code=issue.code,
                severity=issue.severity,
                entity=issue.entity,
                entity_id=issue.entity_id,
                message=issue.message,
            )
            for issue in issues
        ],
    )