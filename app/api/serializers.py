from rest_framework import serializers


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
    percentage = serializers.DecimalField(max_digits=12, decimal_places=6)
    variable = serializers.CharField()
    base = serializers.CharField()


class BDIResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    method = BDIMethodResponseSerializer()
    observation = serializers.CharField()
    quotas = BDIQuotaResponseSerializer(many=True)
