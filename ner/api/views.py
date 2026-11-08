from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ner.models import PluviometricStation
from ner.api.serializers import PluviometricStationResponseSerializer


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
