from rest_framework import serializers

from ner.models import PluviometricStation


class NERCalculationRequestSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-90,
        max_value=90,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-180,
        max_value=180,
    )

    station_count = serializers.IntegerField(
        min_value=2,
        max_value=5,
        required=False,
        default=5,
    )

    adjustment = serializers.IntegerField(
        min_value=-1,
        max_value=1,
        required=False,
        default=0,
    )

    location_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default="",
    )

    location_description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class NERLocationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
    )


class NERCalculationStationResponseSerializer(serializers.Serializer):
    station_id = serializers.IntegerField()

    sequence = serializers.IntegerField()

    station_code = serializers.CharField(
        source="station_code_snapshot",
    )

    station_name = serializers.CharField(
        source="station_name_snapshot",
    )

    latitude = serializers.DecimalField(
        source="latitude_snapshot",
        max_digits=9,
        decimal_places=6,
    )

    longitude = serializers.DecimalField(
        source="longitude_snapshot",
        max_digits=9,
        decimal_places=6,
    )

    nere = serializers.DecimalField(
        source="nere_snapshot",
        max_digits=4,
        decimal_places=2,
    )

    nd = serializers.DecimalField(
        source="nd_snapshot",
        max_digits=10,
        decimal_places=6,
        allow_null=True,
    )

    distance_km = serializers.DecimalField(
        max_digits=14,
        decimal_places=6,
    )

    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=12,
    )

    weighted_nere = serializers.DecimalField(
        max_digits=20,
        decimal_places=12,
    )


class NERCalculationResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    location = NERLocationResponseSerializer()

    station_count = serializers.IntegerField()

    calculation_method = serializers.CharField()

    weighted_nere = serializers.DecimalField(
        max_digits=12,
        decimal_places=6,
    )

    nerp = serializers.IntegerField()

    adjustment = serializers.IntegerField()

    ner = serializers.IntegerField()

    sum_weighted_nere = serializers.DecimalField(
        max_digits=20,
        decimal_places=12,
    )

    sum_weights = serializers.DecimalField(
        max_digits=20,
        decimal_places=12,
    )

    norm_reference = serializers.CharField()

    calculated_at = serializers.DateTimeField()

    stations = NERCalculationStationResponseSerializer(
        many=True,
    )


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