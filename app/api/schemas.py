from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


YEAR_MONTH_DAY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])-01$"


class CompositionItemInputSchema(BaseModel):
    composition_id: str
    reference_base_date: str = Field(
        pattern=YEAR_MONTH_DAY_PATTERN,
    )
    factor: Decimal

class ServiceItemInputSchema(BaseModel):
    id: str
    code: str
    description: str
    unit: str
    quantity: Decimal
    compositions: list[CompositionItemInputSchema]


class BudgetCalculationRequestSchema(BaseModel):
    budget_id: str | None = None
    project_id: str
    source_file_uf: str = Field(
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
    )
    methodology: Literal["SC", "SN"]
    type_system: Literal["ON", "DS", "NA"]
    monetary_base_date: str = Field(
        pattern=YEAR_MONTH_DAY_PATTERN,
    )
    services: list[ServiceItemInputSchema]
    overrides: dict[str, Any] = Field(
        default_factory=dict,
    )


class ValidationIssueResponse(BaseModel):
    code: str
    severity: str
    entity: str
    entity_id: str
    message: str


class CompositionResultResponse(BaseModel):
    composition_id: str
    reference_base_date: str = Field(
        pattern=YEAR_MONTH_DAY_PATTERN,
    )
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
    source_file_uf: str = Field(
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
    )
    methodology: Literal["SC","SN"]
    type_system: Literal["ON","DS","NA"]
    monetary_base_date: str = Field(
        pattern=YEAR_MONTH_DAY_PATTERN,
    )
    total_cost: Decimal
    services: list[ServiceItemResultResponse]


class BudgetCalculationResponse(BaseModel):
    calculation_id: str
    budget: CalculatedBudgetResponse | None
    issues: list[ValidationIssueResponse]