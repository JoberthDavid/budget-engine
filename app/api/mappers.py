from app.domain.models import (
    BudgetCalculationRequest,
    CompositionItemInput,
    ServiceItemInput,
)


def map_composition_item(
    item: dict,
) -> CompositionItemInput:
    return CompositionItemInput(
        composition_id=item["composition_id"],
        reference_base_date=item["reference_base_date"],
        factor=item["factor"],
    )


def map_service_item(
    item: dict,
) -> ServiceItemInput:
    return ServiceItemInput(
        id=item["id"],
        code=item["code"],
        description=item["description"],
        unit=item["unit"],
        quantity=item["quantity"],
        compositions=tuple(
            map_composition_item(composition)
            for composition in item["compositions"]
        ),
    )


def map_budget_calculation_request(
    request: dict,
) -> BudgetCalculationRequest:
    return BudgetCalculationRequest(
        project_id=request["project_id"],
        source_file_uf=request["source_file_uf"],
        methodology=request["methodology"],
        type_system=request["type_system"],
        monetary_base_date=request["monetary_base_date"],
        services=tuple(
            map_service_item(service)
            for service in request["services"]
        ),
        budget_id=request.get("budget_id"),
        overrides=dict(request.get("overrides", {})),
    )
