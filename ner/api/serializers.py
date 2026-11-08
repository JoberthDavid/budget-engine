from rest_framework import serializers

from ner.models import PluviometricStation


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
