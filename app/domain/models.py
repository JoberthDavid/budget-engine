from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class CompositionItemInput:
    composition_id: str
    reference_base_date: str
    factor: Decimal


@dataclass(frozen=True)
class ServiceItemInput:
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    compositions: tuple[CompositionItemInput, ...]


@dataclass(frozen=True)
class BudgetCalculationRequest:
    project_id: str
    methodology: str
    type_system: str
    monetary_base_date: str
    services: tuple[ServiceItemInput, ...]
    budget_id: str | None = None
    overrides: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    entity: str
    entity_id: str
    message: str


@dataclass(frozen=True)
class CompositionResult:
    composition_id: str
    reference_base_date: str
    factor: Decimal
    unit_cost: Decimal
    total_cost: Decimal


@dataclass(frozen=True)
class ServiceItemResult:
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    compositions: tuple[CompositionResult, ...]


@dataclass(frozen=True)
class CalculatedBudget:
    id: str
    project_id: str
    methodology: str
    type_system: str
    monetary_base_date: str
    total_cost: Decimal
    services: tuple[ServiceItemResult, ...]
