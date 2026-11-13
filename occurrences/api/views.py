from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response

from occurrences.api.permissions import (
    HasLocationListScope,
    HasLocationObjectScope,
    HasSupplierListScope,
    HasSupplierObjectScope,
)
from occurrences.api.serializers import (
    SupplierLocationSerializer,
    SupplierSerializer,
)
from occurrences.api.services import save_supplier_location
from occurrences.validators import normalize_state
from security.authentication import ManifoldJWTAuthentication

from django.db.models import Prefetch
from occurrences.models import (
    Supplier,
    SupplierLocation,
    SupplierLocationMaterial,
    SupplierLocationMaterialNature,
)


PUT_DEFAULTS = {
    "trade_name": "",
    "cnpj": None,
    "phone": "",
    "email": "",
    "legal_representative": "",
    "representative_email": "",
    "representative_phone": "",
    "active": True,
}

LOCATION_PUT_DEFAULTS = {
    "street": "",
    "number": "",
    "complement": "",
    "neighborhood": "",
    "postal_code": "",
    "latitude": None,
    "longitude": None,
    "source": "MANUAL",
    "external_reference": "",
    "active": True,
}

def locations_with_related_data(queryset):
    return queryset.prefetch_related(
        Prefetch(
            "material_links",
            queryset=SupplierLocationMaterial.objects.select_related(
                "material",
            ).order_by("material__code"),
            to_attr="prefetched_material_links",
        ),
        Prefetch(
            "nature_links",
            queryset=SupplierLocationMaterialNature.objects.select_related(
                "material_nature",
            ).order_by("material_nature__name"),
            to_attr="prefetched_nature_links",
        ),
    )

def save_supplier(serializer):
    """
    Persiste o fornecedor e converte eventual colisão concorrente
    de CNPJ em erro de validação.
    """
    try:
        with transaction.atomic():
            return serializer.save()

    except IntegrityError:
        cnpj = serializer.validated_data.get("cnpj")

        if cnpj:
            queryset = Supplier.objects.filter(cnpj=cnpj)

            if serializer.instance:
                queryset = queryset.exclude(
                    pk=serializer.instance.pk
                )

            if queryset.exists():
                raise serializers.ValidationError({
                    "cnpj": (
                        "Já existe um fornecedor cadastrado "
                        "com este CNPJ."
                    )
                })

        raise


@api_view(["GET", "POST"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasSupplierListScope])
def list_suppliers(request):
    if request.method == "GET":
        suppliers = Supplier.objects.filter(active=True).order_by(
            "legal_name"
        )
        serializer = SupplierSerializer(suppliers, many=True)
        return Response(serializer.data)

    serializer = SupplierSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    supplier = save_supplier(serializer)

    return Response(
        SupplierSerializer(supplier).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasSupplierObjectScope])
def supplier_detail(request, supplier_id):
    try:
        supplier = Supplier.objects.get(pk=supplier_id)
    except Supplier.DoesNotExist:
        return Response(
            {"detail": "Fornecedor não encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(SupplierSerializer(supplier).data)

    if request.method in ("PUT", "PATCH"):
        data = request.data

        if request.method == "PUT":
            data = {
                **PUT_DEFAULTS,
                **request.data,
            }

        serializer = SupplierSerializer(
            supplier,
            data=data,
            partial=request.method == "PATCH",
        )
        serializer.is_valid(raise_exception=True)
        supplier = save_supplier(serializer)

        return Response(SupplierSerializer(supplier).data)

    supplier.active = False
    supplier.save(update_fields=["active", "updated_at"])

    return Response(status=status.HTTP_204_NO_CONTENT)


def parse_positive_integer(value, parameter_name):
    if value is None:
        return None

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise serializers.ValidationError({
            parameter_name: "Informe um número inteiro válido."
        })

    if parsed < 1:
        raise serializers.ValidationError({
            parameter_name: "O valor deve ser maior que zero."
        })

    return parsed


def filter_locations(queryset, params):
    supplier_id = parse_positive_integer(
        params.get("supplier_id"),
        "supplier_id",
    )

    material_id = parse_positive_integer(
        params.get("material_id"),
        "material_id",
    )

    nature_id = parse_positive_integer(
        params.get("nature_id"),
        "nature_id",
    )

    if supplier_id is not None:
        queryset = queryset.filter(supplier_id=supplier_id)

    state = params.get("state")

    if state:
        try:
            state = normalize_state(state)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({
                "state": exc.messages,
            }) from exc

        queryset = queryset.filter(state=state)

    municipality = params.get("municipality")

    if municipality is not None:
        municipality = municipality.strip()

        if not municipality:
            raise serializers.ValidationError({
                "municipality": "Informe um município válido."
            })

        queryset = queryset.filter(
            municipality__icontains=municipality,
        )

    material_status = params.get(
        "material_status",
        "all",
    ).lower()

    if material_status not in ("all", "active", "inactive"):
        raise serializers.ValidationError({
            "material_status": (
                "Valores permitidos: all, active ou inactive."
            )
        })

    material_filters = {}

    if material_id is not None:
        material_filters["material_links__material_id"] = material_id

    if material_status == "active":
        material_filters["material_links__active"] = True

    elif material_status == "inactive":
        material_filters["material_links__active"] = False

    if material_filters:
        queryset = queryset.filter(**material_filters)

    if nature_id is not None:
        queryset = queryset.filter(
            nature_links__material_nature_id=nature_id,
            nature_links__material_nature__active=True,
        )

    return queryset.distinct()


@api_view(["GET", "POST"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasLocationListScope])
def list_locations(request):
    if request.method == "GET":
        locations = locations_with_related_data(
            SupplierLocation.objects.filter(
                active=True,
            ).select_related(
                "supplier",
            )
        )

        locations = filter_locations(
            locations,
            request.query_params,
        )

        serializer = SupplierLocationSerializer(
            locations,
            many=True,
        )

        return Response(serializer.data)

    serializer = SupplierLocationSerializer(
        data=request.data,
    )
    serializer.is_valid(raise_exception=True)

    location = save_supplier_location(serializer)

    return Response(
        SupplierLocationSerializer(location).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@authentication_classes([ManifoldJWTAuthentication])
@permission_classes([HasLocationObjectScope])
def location_detail(request, location_id):
    try:
        queryset = SupplierLocation.objects.select_related(
            "supplier",
        )

        if request.method == "GET":
            queryset = locations_with_related_data(queryset)

        location = queryset.get(pk=location_id)

    except SupplierLocation.DoesNotExist:
        return Response(
            {"detail": "Unidade não encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(
            SupplierLocationSerializer(location).data,
        )

    if request.method in ("PUT", "PATCH"):
        data = request.data

        if request.method == "PUT":
            data = {
                **LOCATION_PUT_DEFAULTS,
                **request.data,
            }

        serializer = SupplierLocationSerializer(
            location,
            data=data,
            partial=request.method == "PATCH",
        )

        serializer.is_valid(raise_exception=True)

        location = save_supplier_location(
            serializer,
            replace=request.method == "PUT",
        )

        return Response(
            SupplierLocationSerializer(location).data,
        )

    location.active = False
    location.save(update_fields=["active", "updated_at"])

    return Response(status=status.HTTP_204_NO_CONTENT)