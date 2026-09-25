from app.api.schemas import (
    BudgetCalculationRequestSchema,
    CompositionItemInputSchema,
    ServiceItemInputSchema,
)
from app.domain.models import (
    BudgetCalculationRequest,
    CompositionItemInput,
    ServiceItemInput,
)


def map_composition_item(
    item: CompositionItemInputSchema,
) -> CompositionItemInput:
    return CompositionItemInput(
        composition_id=item.composition_id,
        reference_base_date=item.reference_base_date,
        factor=item.factor,
    )


def map_service_item(
    item: ServiceItemInputSchema,
) -> ServiceItemInput:
    return ServiceItemInput(
        id=item.id,
        code=item.code,
        description=item.description,
        unit=item.unit,
        quantity=item.quantity,
        compositions=tuple(
            map_composition_item(composition)
            for composition in item.compositions
        ),
    )

def map_budget_calculation_request(
    request: BudgetCalculationRequestSchema,
) -> BudgetCalculationRequest:
    return BudgetCalculationRequest(
        project_id=request.project_id,
        source_file_uf=request.source_file_uf,
        methodology=request.methodology,
        type_system=request.type_system,
        monetary_base_date=request.monetary_base_date,
        services=tuple(
            map_service_item(service)
            for service in request.services
        ),
        budget_id=request.budget_id,
        overrides=dict(request.overrides),
    )