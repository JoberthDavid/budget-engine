from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from occurrences.models import (
    Material,
    MaterialNature,
    Supplier,
    SupplierLocation,
)
from occurrences.validators import normalize_cnpj, normalize_postal_code, normalize_state


class SupplierSerializer(serializers.ModelSerializer):
    cnpj = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=18,
    )

    class Meta:
        model = Supplier
        fields = (
            "id",
            "legal_name",
            "trade_name",
            "cnpj",
            "phone",
            "email",
            "legal_representative",
            "representative_email",
            "representative_phone",
            "active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_cnpj(self, value):
        try:
            normalized = normalize_cnpj(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

        if normalized:
            queryset = Supplier.objects.filter(cnpj=normalized)

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "Já existe um fornecedor cadastrado com este CNPJ."
                )

        return normalized

    def validate_legal_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "A razão social é obrigatória."
            )

        return value

    def validate_trade_name(self, value):
        return value.strip()

    def validate(self, attrs):
        if self.instance is None and not attrs.get("legal_name"):
            raise serializers.ValidationError({
                "legal_name": "A razão social é obrigatória."
            })

        return attrs


class SupplierLocationSerializer(serializers.ModelSerializer):
    state = serializers.CharField(
        max_length=2,
    )

    nature_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
    )

    material_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
    )

    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
    )

    materials = serializers.SerializerMethodField()
    natures = serializers.SerializerMethodField()

    class Meta:
        model = SupplierLocation
        fields = (
            "id",
            "supplier",
            "name",
            "street",
            "number",
            "complement",
            "neighborhood",
            "municipality",
            "state",
            "postal_code",
            "latitude",
            "longitude",
            "source",
            "external_reference",
            "active",
            "nature_ids",
            "material_ids",
            "materials",
            "natures",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "O nome da unidade é obrigatório."
            )

        return value

    def validate_municipality(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "O município é obrigatório."
            )

        return value

    def validate_state(self, value):
        try:
            return normalize_state(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_postal_code(self, value):
        try:
            return normalize_postal_code(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_latitude(self, value):
        return value

    def validate_longitude(self, value):
        return value

    def validate(self, attrs):
        latitude = attrs.get(
            "latitude",
            self.instance.latitude if self.instance else None,
        )
        longitude = attrs.get(
            "longitude",
            self.instance.longitude if self.instance else None,
        )

        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError({
                "latitude": (
                    "Latitude e longitude devem ser informadas juntas."
                )
            })

        nature_ids = attrs.get("nature_ids")
        if nature_ids is not None:
            if len(nature_ids) != len(set(nature_ids)):
                raise serializers.ValidationError({
                    "nature_ids": "Existem naturezas duplicadas."
                })

            found = set(
                MaterialNature.objects.filter(
                    id__in=nature_ids,
                    active=True,
                ).values_list("id", flat=True)
            )

            missing = set(nature_ids) - found
            if missing:
                raise serializers.ValidationError({
                    "nature_ids": (
                        f"Naturezas inexistentes ou inativas: "
                        f"{sorted(missing)}"
                    )
                })

        material_ids = attrs.get("material_ids")
        if material_ids is not None:
            if len(material_ids) != len(set(material_ids)):
                raise serializers.ValidationError({
                    "material_ids": "Existem materiais duplicados."
                })

            found = set(
                Material.objects.filter(
                    id__in=material_ids,
                ).values_list("id", flat=True)
            )

            missing = set(material_ids) - found
            if missing:
                raise serializers.ValidationError({
                    "material_ids": (
                        f"Materiais inexistentes: {sorted(missing)}"
                    )
                })

        return attrs

    def validate_supplier(self, supplier):
        if self.instance is None:
            if not supplier.active:
                raise serializers.ValidationError(
                    "Não é permitido criar unidade para fornecedor inativo."
                )
            return supplier

        if supplier.pk != self.instance.supplier_id and not supplier.active:
            raise serializers.ValidationError(
                "Não é permitido vincular a unidade a um fornecedor inativo."
            )

        return supplier

    def get_materials(self, obj):
        links = getattr(
            obj,
            "prefetched_material_links",
            None,
        )

        if links is None:
            links = obj.material_links.select_related(
                "material"
            ).order_by("material__code")

        return [
            {
                "id": link.material_id,
                "code": link.material.code,
                "description": link.material.description,
                "unit": link.material.unit,
                "active": link.active,
            }
            for link in links
        ]

    def get_natures(self, obj):
        links = getattr(
            obj,
            "prefetched_nature_links",
            None,
        )

        if links is None:
            links = obj.nature_links.select_related(
                "material_nature"
            ).order_by("material_nature__name")

        return [
            {
                "id": link.material_nature_id,
                "code": link.material_nature.code,
                "name": link.material_nature.name,
            }
            for link in links
        ]
