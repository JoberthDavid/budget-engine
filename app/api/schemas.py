from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class CompositionItemInputSchema(BaseModel):
    composition_id: str
    reference_base_date: str
    factor: Decimal


class ServiceItemInputSchema(BaseModel):
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    compositions: list[CompositionItemInputSchema]


class BudgetCalculationRequestSchema(BaseModel):
    project_id: str
    methodology: Literal["SC","SN"]
    type_system: Literal["ON","DS","NA"]
    monetary_base_date: str
    services: list[ServiceItemInputSchema]
    budget_id: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)


class ValidationIssueResponse(BaseModel):
    code: str
    severity: str
    entity: str
    entity_id: str
    message: str


class CompositionResultResponse(BaseModel):
    composition_id: str
    reference_base_date: str
    factor: Decimal
    unit_cost: Decimal
    total_cost: Decimal


class ServiceItemResultResponse(BaseModel):
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    compositions: list[CompositionResultResponse]


class CalculatedBudgetResponse(BaseModel):
    id: str
    project_id: str
    methodology: Literal["SC","SN"]
    type_system: Literal["ON","DS","NA"]
    monetary_base_date: str
    total_cost: Decimal
    services: list[ServiceItemResultResponse]


class BudgetCalculationResponse(BaseModel):
    calculation_id: str
    budget: CalculatedBudgetResponse | None
    issues: list[ValidationIssueResponse]