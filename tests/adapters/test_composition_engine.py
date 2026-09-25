from decimal import Decimal
from unittest.mock import Mock

from app.adapters.composition_engine import (
    CompositionEngineAdapter,
)


def test_adapter_calcula_composicao():
    session = Mock()

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "composition_id": "4011209",
        "methodology":"SC",
        "reference_base_date": "2025-07-01",
        "unit_cost": "123.4567",
    }

    session.post.return_value = response

    adapter = CompositionEngineAdapter(
        base_url="https://composition-engine.example",
        api_key="secret",
        session=session,
    )

    result = adapter.calculate(
        source_file_uf="GO",
        methodology="SC",
        type_system="ON",
        monetary_base_date="2026-07-01",
        composition_id="4011209",
        reference_base_date="2025-07-01",
        overrides={},
    )

    assert result.composition_id == "4011209"
    assert result.reference_base_date == "2025-07-01"
    assert result.unit_cost == Decimal("123.4567")

    session.post.assert_called_once()