from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.domain.models import (
    BudgetCalculationRequest,
    CalculatedBudget,
    CompositionResult,
    ServiceItemResult,
    ValidationIssue,
)
from app.ports.composition_calculator import CompositionCalculatorPort


class CalculateBudget:
    """Caso de uso do cálculo oficial do Budget."""

    def __init__(self, composition_calculator: CompositionCalculatorPort) -> None:
        self._composition_calculator = composition_calculator

    def execute(
        self, request: BudgetCalculationRequest
    ) -> tuple[str, CalculatedBudget | None, list[ValidationIssue]]:
        calculation_id = str(uuid4())
        issues: list[ValidationIssue] = []
        service_results: list[ServiceItemResult] = []

        for service in request.services:
            composition_results: list[CompositionResult] = []

            for item in service.compositions:
                try:
                    calculated = self._composition_calculator.calculate(
                        source_file_uf=request.source_file_uf,
                        methodology=request.methodology,
                        type_system=request.type_system,
                        monetary_base_date=request.monetary_base_date,
                        composition_id=item.composition_id,
                        reference_base_date=item.reference_base_date,
                        overrides=request.overrides,
                    )
                except NotImplementedError:
                    raise
                except Exception as exc:
                    issues.append(
                        ValidationIssue(
                            code="COMPOSITION_CALCULATION_ERROR",
                            severity="CRITICAL",
                            entity="CompositionItem",
                            entity_id=item.composition_id,
                            message=str(exc),
                        )
                    )
                    continue

                total_cost = (calculated.unit_cost * item.factor * service.quantity).quantize(
                    Decimal("0.01")
                )
                composition_results.append(
                    CompositionResult(
                        composition_id=item.composition_id,
                        reference_base_date=item.reference_base_date,
                        factor=item.factor,
                        unit_cost=calculated.unit_cost,
                        total_cost=total_cost,
                    )
                )

            service_total = sum((x.total_cost for x in composition_results), Decimal("0.00"))
            unit_cost = (
                (service_total / service.quantity).quantize(Decimal("0.01"))
                if service.quantity > 0
                else Decimal("0.00")
            )

            if service.quantity == 0:
                issues.append(
                    ValidationIssue(
                        code="SERVICE_ITEM_ZERO_QUANTITY",
                        severity="CRITICAL",
                        entity="ServiceItem",
                        entity_id=service.id,
                        message="Informe uma quantidade maior que zero ou remova o ServiceItem.",
                    )
                )

            service_results.append(
                ServiceItemResult(
                    id=service.id,
                    code=service.code,
                    description=service.description,
                    unit=service.unit,
                    quantity=service.quantity,
                    unit_cost=unit_cost,
                    total_cost=service_total,
                    compositions=tuple(composition_results),
                )
            )

        if any(issue.severity == "CRITICAL" for issue in issues):
            return calculation_id, None, issues

        total = sum((s.total_cost for s in service_results), Decimal("0.00"))
        budget = CalculatedBudget(
            id=request.budget_id or str(uuid4()),
            project_id=request.project_id,
            source_file_uf=request.source_file_uf,
            methodology=request.methodology,
            type_system=request.type_system,
            monetary_base_date=request.monetary_base_date,
            total_cost=total,
            services=tuple(service_results),
        )
        return calculation_id, budget, issues