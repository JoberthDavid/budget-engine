from functools import lru_cache

from django.db.models import Prefetch
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status

from app.adapters.composition_engine import CompositionEngineAdapter
from app.models import BDI, BDIQuota, BDIMethod
from app.api.mappers import map_budget_calculation_request
from app.api.serializers import (
    BDICreateSerializer,
    BDIResponseSerializer,
    BudgetCalculationRequestSerializer,
    BudgetCalculationResponseSerializer,
)
from app.application.calculate_budget import CalculateBudget


@lru_cache(maxsize=1)
def get_calculate_budget() -> CalculateBudget:
    return CalculateBudget(CompositionEngineAdapter())


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET", "POST"])
def list_bdis(request):
    if request.method == "GET":
        bdis = (
            BDI.objects
            .select_related("method")
            .prefetch_related(
                Prefetch(
                    "quotas",
                    queryset=BDIQuota.objects.order_by("id"),
                )
            )
            .order_by("id")
        )
        return Response(
            BDIResponseSerializer(bdis, many=True).data
        )

    serializer = BDICreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    try:
        method = BDIMethod.objects.get(id=data["method_id"])
    except BDIMethod.DoesNotExist:
        return Response(
            {"detail": "Método de BDI não encontrado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        bdi = BDI.objects.create(
            name=data["name"],
            slug=data["slug"],
            method=method,
            observation=data.get("observation", ""),
        )

        BDIQuota.objects.bulk_create(
            [
                BDIQuota(
                    bdi=bdi,
                    group=quota["group"],
                    description=quota["description"],
                    percentage=quota["percentage"],
                    variable=quota["variable"],
                    base=quota["base"],
                )
                for quota in data["quotas"]
            ]
        )

    bdi = (
        BDI.objects
        .select_related("method")
        .prefetch_related(
            Prefetch(
                "quotas",
                queryset=BDIQuota.objects.order_by("id"),
            )
        )
        .get(id=bdi.id)
    )

    return Response(
        BDIResponseSerializer(bdi).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def get_bdi(request, bdi_id):
    bdi = (
        BDI.objects
        .select_related("method")
        .prefetch_related(
            Prefetch(
                "quotas",
                queryset=BDIQuota.objects.order_by("id"),
            )
        )
        .filter(id=bdi_id)
        .first()
    )

    if bdi is None:
        return Response(
            {"detail": "BDI não encontrado."},
            status=404,
        )

    return Response(
        BDIResponseSerializer(bdi).data
    )


@api_view(["POST"])
def calculate_budget(request):
    request_serializer = BudgetCalculationRequestSerializer(data=request.data)
    request_serializer.is_valid(raise_exception=True)

    calculation_request = map_budget_calculation_request(
        request_serializer.validated_data
    )
    calculation_id, budget, issues = get_calculate_budget().execute(
        calculation_request
    )

    budget_data = None
    if budget is not None:
        budget_data = {
            "id": budget.id,
            "project_id": budget.project_id,
            "source_file_uf": budget.source_file_uf,
            "methodology": budget.methodology,
            "type_system": budget.type_system,
            "monetary_base_date": budget.monetary_base_date,
            "total_cost": budget.total_cost,
            "services": [
                {
                    "id": service.id,
                    "code": service.code,
                    "description": service.description,
                    "unit": service.unit,
                    "quantity": service.quantity,
                    "unit_cost": service.unit_cost,
                    "total_cost": service.total_cost,
                    "compositions": [
                        {
                            "composition_id": composition.composition_id,
                            "reference_base_date": composition.reference_base_date,
                            "factor": composition.factor,
                            "unit_cost": composition.unit_cost,
                            "total_cost": composition.total_cost,
                        }
                        for composition in service.compositions
                    ],
                }
                for service in budget.services
            ],
        }

    response_data = BudgetCalculationResponseSerializer(
        {
            "calculation_id": calculation_id,
            "budget": budget_data,
            "issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "entity": issue.entity,
                    "entity_id": issue.entity_id,
                    "message": issue.message,
                }
                for issue in issues
            ],
        }
    ).data
    return Response(response_data)
