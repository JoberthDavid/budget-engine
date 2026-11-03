from decimal import Decimal
from unittest.mock import Mock, patch

from rest_framework.test import APIClient
from app.domain.models import (
    CalculatedBudget,
    CompositionResult,
    ServiceItemResult,
    ValidationIssue,
)


class _ApiClient:
    def __init__(self, calculate_budget=None):
        self.calculate_budget = calculate_budget

    def post(self, path, *, json):
        with patch(
            "app.api.views.get_calculate_budget",
            return_value=self.calculate_budget,
        ):
            return APIClient().post(path, json, format="json")


def test_calculate_rejects_missing_required_fields():
    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-001",
        None,
        [],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={},
    )

    assert response.status_code == 400
    calculate_budget.execute.assert_not_called()


def test_calculate_route_exists_before_engine_wiring():
    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-001",
        None,
        [],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [
                {
                    "id": "service-001",
                    "code": "SERV-001",
                    "description": "Execução",
                    "unit": "m²",
                    "quantity": "1000",
                    "compositions": [
                        {
                            "composition_id": "composition-001",
                            "reference_base_date": "2025-07-01",
                            "factor": "1",
                        }
                    ],
                }
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["calculation_id"] == "CALC-001"
    assert body["budget"] is None
    assert body["issues"] == []

    calculate_budget.execute.assert_called_once()


def test_calculate_maps_http_request_to_domain_request():
    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-001",
        None,
        [],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 200

    calculation_request = (
        calculate_budget.execute.call_args.args[0]
    )

    assert calculation_request.project_id == "project-001"
    assert calculation_request.methodology == "SC"
    assert calculation_request.type_system == "ON"
    assert calculation_request.monetary_base_date == "2026-07-01"
    assert calculation_request.services == ()
    assert calculation_request.overrides == {}
    assert calculation_request.source_file_uf == "DF"


def test_calculate_serializes_complete_budget_response():
    budget = CalculatedBudget(
        id="budget-001",
        project_id="project-001",
        source_file_uf="DF",
        methodology="SC",
        type_system="ON",
        monetary_base_date="2026-07-01",
        total_cost=Decimal("123456.78"),
        services=(
            ServiceItemResult(
                id="service-001",
                code="SERV-001",
                description="Execução de serviço",
                unit="m²",
                quantity=Decimal("100.00"),
                unit_cost=Decimal("1234.56"),
                total_cost=Decimal("123456.00"),
                compositions=(
                    CompositionResult(
                        composition_id="composition-001",
                        reference_base_date="2025-07-01",
                        factor=Decimal("1.0000"),
                        unit_cost=Decimal("1234.56"),
                        total_cost=Decimal("123456.00"),
                    ),
                ),
            ),
        ),
    )

    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-001",
        budget,
        [],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["calculation_id"] == "CALC-001"

    assert body["budget"]["id"] == "budget-001"
    assert body["budget"]["project_id"] == "project-001"
    assert body["budget"]["methodology"] == "SC"
    assert body["budget"]["type_system"] == "ON"
    assert body["budget"]["monetary_base_date"] == "2026-07-01"
    assert body["budget"]["total_cost"] == "123456.78"

    assert len(body["budget"]["services"]) == 1

    service = body["budget"]["services"][0]

    assert service["id"] == "service-001"
    assert service["code"] == "SERV-001"
    assert service["description"] == "Execução de serviço"
    assert service["unit"] == "m²"
    assert service["quantity"] == "100.00"
    assert service["unit_cost"] == "1234.56"
    assert service["total_cost"] == "123456.00"

    assert len(service["compositions"]) == 1

    composition = service["compositions"][0]

    assert composition["composition_id"] == "composition-001"
    assert composition["reference_base_date"] == "2025-07-01"
    assert composition["factor"] == "1.0000"
    assert composition["unit_cost"] == "1234.56"
    assert composition["total_cost"] == "123456.00"

    assert body["issues"] == []


def test_calculate_serializes_validation_issues():
    issues = [
        ValidationIssue(
            code="SERVICE_ITEM_ZERO_QUANTITY",
            severity="CRITICAL",
            entity="ServiceItem",
            entity_id="service-001",
            message=(
                "Informe uma quantidade maior que zero "
                "ou remova o ServiceItem."
            ),
        ),
        ValidationIssue(
            code="COMPOSITION_WARNING",
            severity="WARNING",
            entity="CompositionItem",
            entity_id="composition-001",
            message="Composição possui uma ressalva.",
        ),
    ]

    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-002",
        None,
        issues,
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["calculation_id"] == "CALC-002"
    assert body["budget"] is None

    assert body["issues"] == [
        {
            "code": "SERVICE_ITEM_ZERO_QUANTITY",
            "severity": "CRITICAL",
            "entity": "ServiceItem",
            "entity_id": "service-001",
            "message": (
                "Informe uma quantidade maior que zero "
                "ou remova o ServiceItem."
            ),
        },
        {
            "code": "COMPOSITION_WARNING",
            "severity": "WARNING",
            "entity": "CompositionItem",
            "entity_id": "composition-001",
            "message": "Composição possui uma ressalva.",
        },
    ]


def test_critical_validation_issue_returns_http_200_with_null_budget():
    issue = ValidationIssue(
        code="SERVICE_ITEM_ZERO_QUANTITY",
        severity="CRITICAL",
        entity="ServiceItem",
        entity_id="service-001",
        message="Quantidade inválida.",
    )

    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-003",
        None,
        [issue],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["calculation_id"] == "CALC-003"
    assert body["budget"] is None
    assert len(body["issues"]) == 1
    assert body["issues"][0]["severity"] == "CRITICAL"


def test_calculate_preserves_decimal_precision_in_response():
    budget = CalculatedBudget(
        id="budget-precision",
        project_id="project-001",
        source_file_uf="DF",
        methodology="SC",
        type_system="ON",
        monetary_base_date="2026-07-01",
        total_cost=Decimal("0.10"),
        services=(
            ServiceItemResult(
                id="service-001",
                code="SERV-001",
                description="Serviço",
                unit="un",
                quantity=Decimal("3"),
                unit_cost=Decimal("0.033333333333"),
                total_cost=Decimal("0.10"),
                compositions=(),
            ),
        ),
    )

    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-PRECISION",
        budget,
        [],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["budget"]["total_cost"] == "0.10"

    assert (
        body["budget"]["services"][0]["unit_cost"]
        == "0.033333333333"
    )

    assert (
        body["budget"]["services"][0]["total_cost"]
        == "0.10"
    )


def test_api_uses_injected_calculate_budget():
    calculate_budget = Mock()

    calculate_budget.execute.return_value = (
        "CALC-DI",
        None,
        [],
    )

    client = _ApiClient(calculate_budget)

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["calculation_id"] == "CALC-DI"

    calculate_budget.execute.assert_called_once()

def test_calculate_rejects_invalid_methodology():
    client = _ApiClient()

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "XX",
            "type_system": "ON",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


def test_calculate_rejects_invalid_type_system():
    client = _ApiClient()

    response = client.post(
        "/budgets/calculate",
        json={
            "project_id": "project-001",
            "source_file_uf": "DF",
            "methodology": "SC",
            "type_system": "XX",
            "monetary_base_date": "2026-07-01",
            "services": [],
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
