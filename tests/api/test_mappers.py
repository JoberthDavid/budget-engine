from decimal import Decimal

from app.api.mappers import map_budget_calculation_request
from app.api.schemas import BudgetCalculationRequestSchema
from app.domain.models import (
    BudgetCalculationRequest,
    CompositionItemInput,
    ServiceItemInput,
)


def make_request_schema() -> BudgetCalculationRequestSchema:
    return BudgetCalculationRequestSchema.model_validate(
        {
            "project_id": "PROJ-001",
            "budget_id": "ORC-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-01-01",
            "services": [
                {
                    "id": "SERV-001",
                    "code": "4011209",
                    "description": "Execução de serviço",
                    "unit": "m3",
                    "quantity": "100.00",
                    "compositions": [
                        {
                            "composition_id": "4011209",
                            "reference_base_date": "2026-01-01",
                            "factor": "1.50",
                        }
                    ],
                }
            ],
            "overrides": {
                "test_override": "value",
            },
        }
    )


def test_mapper_returns_budget_calculation_request():
    request = map_budget_calculation_request(
        make_request_schema()
    )

    assert isinstance(request, BudgetCalculationRequest)


def test_mapper_converts_services_list_to_tuple():
    request = map_budget_calculation_request(
        make_request_schema()
    )

    assert isinstance(request.services, tuple)
    assert len(request.services) == 1
    assert isinstance(request.services[0], ServiceItemInput)


def test_mapper_converts_compositions_list_to_tuple():
    request = map_budget_calculation_request(
        make_request_schema()
    )

    service = request.services[0]

    assert isinstance(service.compositions, tuple)
    assert len(service.compositions) == 1
    assert isinstance(
        service.compositions[0],
        CompositionItemInput,
    )


def test_mapper_preserves_decimal_values():
    request = map_budget_calculation_request(
        make_request_schema()
    )

    service = request.services[0]
    composition = service.compositions[0]

    assert isinstance(service.quantity, Decimal)
    assert service.quantity == Decimal("100.00")

    assert isinstance(composition.factor, Decimal)
    assert composition.factor == Decimal("1.50")


def test_mapper_preserves_request_values():
    request = map_budget_calculation_request(
        make_request_schema()
    )

    assert request.project_id == "PROJ-001"
    assert request.budget_id == "ORC-001"
    assert request.methodology == "SC"
    assert request.type_system == "ON"
    assert request.monetary_base_date == "2026-01-01"

    service = request.services[0]

    assert service.id == "SERV-001"
    assert service.code == "4011209"
    assert service.description == "Execução de serviço"
    assert service.unit == "m3"

    composition = service.compositions[0]

    assert composition.composition_id == "4011209"
    assert composition.reference_base_date == "2026-01-01"


def test_mapper_copies_overrides_without_interpreting_them():
    schema = make_request_schema()

    request = map_budget_calculation_request(schema)

    assert request.overrides == {
        "test_override": "value",
    }

    assert request.overrides is not schema.overrides

def test_mapper_preserves_minimal_request_defaults():
    schema = BudgetCalculationRequestSchema.model_validate(
        {
            "project_id": "PROJ-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-01-01",
            "services": [],
        }
    )

    request = map_budget_calculation_request(schema)

    assert isinstance(request, BudgetCalculationRequest)

    assert request.project_id == "PROJ-001"
    assert request.methodology == "SC"
    assert request.type_system == "ON"
    assert request.monetary_base_date == "2026-01-01"

    assert request.services == ()
    assert isinstance(request.services, tuple)

    assert request.budget_id is None

    assert request.overrides == {}
    assert isinstance(request.overrides, dict)

def test_mapper_creates_independent_overrides_for_minimal_request():
    schema = BudgetCalculationRequestSchema.model_validate(
        {
            "project_id": "PROJ-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-01-01",
            "services": [],
        }
    )

    request = map_budget_calculation_request(schema)

    assert request.overrides == {}
    assert request.overrides is not schema.overrides