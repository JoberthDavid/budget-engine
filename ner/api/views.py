from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ner.api.serializers import (
    NERCalculationRequestSerializer,
    NERCalculationResponseSerializer,
    PluviometricStationResponseSerializer,
)
from ner.application.calculate_ner import CalculateNERService
from ner.application.save_ner_calculation import (
    SaveNERCalculationService,
)
from ner.domain.exceptions import (
    NERCalculationError,
)
from ner.models import (
    MowingWorkloadCalculation,
    PluviometricStation,
)


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


@api_view(["POST"])
def create_ner_calculation(request):
    request_serializer = NERCalculationRequestSerializer(
        data=request.data,
    )

    request_serializer.is_valid(raise_exception=True)

    data = request_serializer.validated_data

    try:
        result = CalculateNERService().execute(
            latitude=data["latitude"],
            longitude=data["longitude"],
            station_count=data["station_count"],
            adjustment=data["adjustment"],
        )

        calculation = SaveNERCalculationService().execute(
            result=result,
            location_name=data["location_name"],
            location_description=data["location_description"],
        )

    except NERCalculationError as exc:
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except DjangoValidationError as exc:
        detail = (
            exc.message_dict
            if hasattr(exc, "message_dict")
            else exc.messages
        )

        return Response(
            {"detail": detail},
            status=status.HTTP_400_BAD_REQUEST,
        )

    calculation = (
        MowingWorkloadCalculation.objects
        .select_related("location")
        .prefetch_related("stations")
        .get(pk=calculation.pk)
    )

    response_serializer = NERCalculationResponseSerializer(
        calculation,
    )

    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )
