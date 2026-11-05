from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CalculatedComposition:
    composition_id: str
    reference_base_date: str
    unit_cost: Decimal


class CompositionCalculatorPort:
    """Porta para o composition-engine. O domínio não conhece o framework nem HTTP."""

    def calculate(
        self,
        *,
        source_file_uf: str,
        methodology: str,
        type_system: str,
        monetary_base_date: str,
        composition_id: str,
        reference_base_date: str,
        overrides: dict,
    ) -> CalculatedComposition:
        raise NotImplementedError
    

class CompositionProviderError(RuntimeError):
    """Erro abstrato de um fornecedor de cálculo de composição."""


class CompositionNotFoundError(CompositionProviderError):
    pass


class CompositionEngineAuthenticationError(
    CompositionProviderError
):
    pass


class CompositionProviderUnavailableError(
    CompositionProviderError
):
    pass


class CompositionProviderRequestError(
    CompositionProviderError
):
    pass


class CompositionEngineContractError(
    CompositionProviderError
):
    pass


class CompositionEngineConfigurationError(
    CompositionProviderError
):
    pass


class CompositionOverridesUnsupportedError(
    CompositionProviderError
):
    pass