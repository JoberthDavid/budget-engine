from __future__ import annotations

from decimal import Decimal
from os import getenv
from urllib.parse import quote

import requests
from pydantic import BaseModel, ValidationError

from app.ports.composition_calculator import (
    CalculatedComposition,
    CompositionCalculatorPort,
    CompositionEngineAuthenticationError,
    CompositionEngineConfigurationError,
    CompositionEngineContractError,
    CompositionNotFoundError,
    CompositionProviderRequestError,
    CompositionProviderUnavailableError,
    CompositionOverridesUnsupportedError,
)


class _CompositionEngineResponse(BaseModel):
    composition_id: str
    reference_base_date: str
    unit_cost: Decimal


class CompositionEngineAdapter(CompositionCalculatorPort):
    """Adapter HTTP para o composition-engine."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (
            base_url
            if base_url is not None
            else getenv("COMPOSITION_ENGINE_BASE_URL", "")
        ).rstrip("/")

        self.api_key = (
            api_key
            if api_key is not None
            else getenv("COMPOSITION_ENGINE_API_KEY", "")
        )

        self.timeout = timeout
        self.session = session or requests.Session()

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
        self._validate_configuration()

        if overrides:
            raise CompositionOverridesUnsupportedError(
                "O composition-engine atual ainda não possui "
                "contrato para aplicação de overrides."
            )

        endpoint = (
            f"{self.base_url}/compositions/"
            f"{quote(composition_id, safe='')}/calculate"
        )

        params = {
            "source_file_uf": source_file_uf,
            "methodology": methodology,
            "type_system": type_system,
            "monetary_base_date": monetary_base_date,
            "reference_base_date": reference_base_date,
        }

        headers = {
            "X-API-Key": self.api_key,
        }

        try:
            response = self.session.post(
                endpoint,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise CompositionProviderUnavailableError(
                "Tempo limite excedido ao consultar o composition-engine."
            ) from exc
        except requests.RequestException as exc:
            raise CompositionProviderUnavailableError(
                "Não foi possível comunicar com o composition-engine."
            ) from exc

        if response.status_code == 401:
            raise CompositionEngineAuthenticationError(
                "O composition-engine rejeitou a chave de API."
            )

        if response.status_code == 404:
            raise CompositionNotFoundError(
                f"Composição não encontrada: {composition_id}"
            )

        if response.status_code in {400, 422}:
            raise CompositionProviderRequestError(
                "O composition-engine rejeitou os parâmetros da solicitação."
            )

        if response.status_code >= 500:
            raise CompositionProviderUnavailableError(
                f"composition-engine retornou HTTP {response.status_code}."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise CompositionEngineContractError(
                "O composition-engine retornou JSON inválido."
            ) from exc

        try:
            result = _CompositionEngineResponse.model_validate(payload)
        except ValidationError as exc:
            raise CompositionEngineContractError(
                "Resposta incompatível com o contrato do composition-engine."
            ) from exc

        return CalculatedComposition(
            composition_id=result.composition_id,
            reference_base_date=result.reference_base_date,
            unit_cost=result.unit_cost,
        )

    def _validate_configuration(self) -> None:
        if not self.base_url:
            raise CompositionEngineConfigurationError(
                "COMPOSITION_ENGINE_BASE_URL não configurada."
            )

        if not self.api_key:
            raise CompositionEngineConfigurationError(
                "COMPOSITION_ENGINE_API_KEY não configurada."
            )