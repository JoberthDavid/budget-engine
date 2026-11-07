from functools import lru_cache

from django.db.models import Prefetch
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from rest_framework import status

from app.adapters.composition_engine import CompositionEngineAdapter
from app.models import (
    BDI,
    BDIQuota,
    BDIMethod,
    PluviometricStation,
)
from app.api.mappers import map_budget_calculation_request
from app.api.serializers import (
    BDICreateSerializer,
    BDIResponseSerializer,
    BudgetCalculationRequestSerializer,
    BudgetCalculationResponseSerializer,
    BDIUpdateSerializer,
    BDIMethodResponseSerializer,
    PluviometricStationResponseSerializer,
)
from app.application.calculate_budget import CalculateBudget

from app.api.services.bdi_service import (
    BDIService,
    BDIInUseError,
)


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
            .prefetch_related("quotas")
            .order_by("id")
        )

        return Response(
            BDIResponseSerializer(
                bdis,
                many=True
            ).data
        )

    serializer = BDICreateSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    bdi = BDIService.create(
        serializer.validated_data
    )

    return Response(
        BDIResponseSerializer(bdi).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "DELETE"])
def get_bdi(request, bdi_id):

    try:

        bdi = BDI.objects.get(
            pk=bdi_id
        )

    except BDI.DoesNotExist:

        return Response(
            {"detail": "BDI não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":

        bdi = BDIService._load(bdi.id)

        return Response(
            BDIResponseSerializer(bdi).data
        )

    if request.method == "PUT":

        serializer = BDIUpdateSerializer(
            data=request.data,
            context={"instance": bdi},
        )

        serializer.is_valid(
            raise_exception=True
        )

        bdi = BDIService.update(
            bdi.id,
            serializer.validated_data,
        )

        return Response(
            BDIResponseSerializer(bdi).data
        )

    if request.method == "DELETE":

        try:

            BDIService.delete(
                bdi.id
            )

        except BDIInUseError:

            return Response(
                {
                    "code": "BDI_IN_USE",
                    "message": (
                        "Não é possível excluir este BDI "
                        "porque ele está vinculado "
                        "a um ou mais orçamentos."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(["GET"])
def list_bdi_methods(request):

    methods = BDIMethod.objects.order_by("id")

    return Response(
        BDIMethodResponseSerializer(
            methods,
            many=True
        ).data
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

@api_view(["GET"])
def list_ner_stations(request):
    stations = PluviometricStation.objects.all()

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    municipality = request.query_params.get("municipality")
    search = request.query_params.get("search")

    if code:
        stations = stations.filter(code=code.strip())

    if state:
        stations = stations.filter(state__iexact=state.strip())

    if municipality:
        stations = stations.filter(
            municipality__icontains=municipality.strip()
        )

    if search:
        search = search.strip()

        stations = stations.filter(
            Q(code__icontains=search)
            | Q(name__icontains=search)
            | Q(municipality__icontains=search)
            | Q(state__icontains=search)
        )

    stations = stations.order_by("code")

    serializer = PluviometricStationResponseSerializer(
        stations,
        many=True,
    )

    return Response(serializer.data)