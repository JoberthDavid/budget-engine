from rest_framework import serializers
from django.utils.text import slugify

from app.models import BDI, BDIMethod, PluviometricStation

YEAR_MONTH_DAY_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])-01$"


class CompositionItemInputSerializer(serializers.Serializer):
    composition_id = serializers.CharField(allow_blank=True)
    reference_base_date = serializers.RegexField(YEAR_MONTH_DAY_PATTERN)
    factor = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        coerce_to_string=False,
    )


class ServiceItemInputSerializer(serializers.Serializer):
    id = serializers.CharField(allow_blank=True)
    code = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    unit = serializers.CharField(allow_blank=True)
    quantity = serializers.DecimalField(
        max_digits=None,
        decimal_places=None,
        coerce_to_string=False,
    )
    compositions = CompositionItemInputSerializer(many=True)


class BudgetCalculationRequestSerializer(serializers.Serializer):
    budget_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    project_id = serializers.CharField(allow_blank=True)
    source_file_uf = serializers.RegexField(r"^[A-Z]{2}$", min_length=2, max_length=2)
    methodology = serializers.ChoiceField(choices=("SC", "SN"))
    type_system = serializers.ChoiceField(choices=("ON", "DS", "NA"))
    monetary_base_date = serializers.RegexField(YEAR_MONTH_DAY_PATTERN)
    services = ServiceItemInputSerializer(many=True)
    overrides = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
        default=dict,
    )


class ValidationIssueResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    severity = serializers.CharField()
    entity = serializers.CharField()
    entity_id = serializers.CharField()
    message = serializers.CharField()


class CompositionResultResponseSerializer(serializers.Serializer):
    composition_id = serializers.CharField()
    reference_base_date = serializers.RegexField(YEAR_MONTH_DAY_PATTERN)
    factor = serializers.DecimalField(max_digits=None, decimal_places=None)
    unit_cost = serializers.DecimalField(max_digits=None, decimal_places=None)
    total_cost = serializers.DecimalField(max_digits=None, decimal_places=None)


class ServiceItemResultResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    code = serializers.CharField()
    description = serializers.CharField()
    unit = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=None, decimal_places=None)
    unit_cost = serializers.DecimalField(max_digits=None, decimal_places=None)
    total_cost = serializers.DecimalField(max_digits=None, decimal_places=None)
    compositions = CompositionResultResponseSerializer(many=True)


class CalculatedBudgetResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    project_id = serializers.CharField()
    source_file_uf = serializers.RegexField(r"^[A-Z]{2}$", min_length=2, max_length=2)
    methodology = serializers.ChoiceField(choices=("SC", "SN"))
    type_system = serializers.ChoiceField(choices=("ON", "DS", "NA"))
    monetary_base_date = serializers.RegexField(YEAR_MONTH_DAY_PATTERN)
    total_cost = serializers.DecimalField(max_digits=None, decimal_places=None)
    services = ServiceItemResultResponseSerializer(many=True)


class BudgetCalculationResponseSerializer(serializers.Serializer):
    calculation_id = serializers.CharField()
    budget = CalculatedBudgetResponseSerializer(allow_null=True)
    issues = ValidationIssueResponseSerializer(many=True)


class BDIMethodResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    method = serializers.CharField()


class BDIQuotaResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    group = serializers.CharField()
    description = serializers.CharField()
    percentage = serializers.DecimalField(
        max_digits=12,
        decimal_places=6,
    )
    variable = serializers.CharField()
    base = serializers.CharField()


class BDIResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    method = BDIMethodResponseSerializer()
    observation = serializers.CharField()
    quotas = BDIQuotaResponseSerializer(many=True)


class BDIQuotaInputSerializer(serializers.Serializer):
    group = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=200)

    percentage = serializers.DecimalField(
        max_digits=12,
        decimal_places=6,
    )

    variable = serializers.CharField(max_length=100)

    base = serializers.ChoiceField(
        choices=("CD", "PV"),
    )


class BDIAggregateInputSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=150)

    slug = serializers.SlugField(max_length=150)

    method_id = serializers.IntegerField()

    observation = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    quotas = BDIQuotaInputSerializer(
        many=True,
    )

    def validate_method_id(self, value):
        if not BDIMethod.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Método de BDI não encontrado."
            )

        return value

    def validate_slug(self, value):

        queryset = BDI.objects.filter(slug=value)

        instance = self.context.get("instance")

        if instance:
            queryset = queryset.exclude(pk=instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um BDI com este slug."
            )

        return value

    def validate_quotas(self, quotas):

        for quota in quotas:

            if quota["percentage"] < 0:
                raise serializers.ValidationError(
                    "O percentual da quota não pode ser negativo."
                )

        return quotas


class BDICreateSerializer(BDIAggregateInputSerializer):
    pass


class BDIUpdateSerializer(BDIAggregateInputSerializer):
    pass


class PluviometricStationResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluviometricStation
        fields = (
            "id",
            "code",
            "name",
            "municipality",
            "state",
            "operator",
            "latitude",
            "longitude",
            "nd",
            "nere",
            "norm_reference",
        )