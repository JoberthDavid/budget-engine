from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from bdi.models import BDI, BDIMethod
from bdi.api.serializers import (
    BDICreateSerializer,
    BDIResponseSerializer,
    BDIUpdateSerializer,
    BDIMethodResponseSerializer,
)
from bdi.services.bdi_service import (
    BDIService,
    BDIInUseError,
)
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from security.authentication import ManifoldJWTAuthentication

from bdi.api.permissions import (
    HasBDIListScope,
    HasBDIObjectScope,
    HasBDIReadScope,
)


@api_view(["GET", "POST"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasBDIListScope])
def list_bdis(request):
    if request.method == "GET":
        bdis = (
            BDI.objects
            .select_related("method")
            .prefetch_related("quotas")
            .order_by("id")
        )

        return Response(
            BDIResponseSerializer(bdis, many=True).data
        )

    serializer = BDICreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    bdi = BDIService.create(serializer.validated_data)

    return Response(
        BDIResponseSerializer(bdi).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "DELETE"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasBDIObjectScope])
def get_bdi(request, bdi_id):
    try:
        bdi = BDI.objects.get(pk=bdi_id)
    except BDI.DoesNotExist:
        return Response(
            {"detail": "BDI não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        bdi = BDIService._load(bdi.id)
        return Response(BDIResponseSerializer(bdi).data)

    if request.method == "PUT":
        serializer = BDIUpdateSerializer(
            data=request.data,
            context={"instance": bdi},
        )
        serializer.is_valid(raise_exception=True)

        bdi = BDIService.update(
            bdi.id,
            serializer.validated_data,
        )

        return Response(BDIResponseSerializer(bdi).data)

    try:
        BDIService.delete(bdi.id)
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

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasBDIReadScope])
def list_bdi_methods(request):
    methods = BDIMethod.objects.order_by("id")

    return Response(
        BDIMethodResponseSerializer(methods, many=True).data
    )
