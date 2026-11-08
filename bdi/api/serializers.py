from rest_framework import serializers

from bdi.models import BDI, BDIMethod


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
    quotas = BDIQuotaInputSerializer(many=True)

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
