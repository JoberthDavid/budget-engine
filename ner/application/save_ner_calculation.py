from django.core.exceptions import ValidationError
from django.db import transaction

from ner.models import (
    MowingWorkloadCalculation,
    MowingWorkloadCalculationStation,
    MowingWorkloadLocation,
    PluviometricStation,
)


class SaveNERCalculationService:

    @transaction.atomic
    def execute(
        self,
        result,
        location_name="",
        location_description="",
    ):
        location = MowingWorkloadLocation(
            name=location_name,
            description=location_description,
            latitude=result.latitude,
            longitude=result.longitude,
        )
        location.full_clean()
        location.save()

        calculation = MowingWorkloadCalculation(
            location=location,
            station_count=result.station_count,
            calculation_method=result.calculation_method,
            weighted_nere=result.weighted_nere,
            nerp=result.nerp,
            adjustment=result.adjustment,
            ner=result.ner,
            sum_weighted_nere=result.sum_weighted_nere,
            sum_weights=result.sum_weights,
        )

        calculation.full_clean()
        calculation.save()

        selected_stations = [
            item
            for item in result.stations
            if item.considered
        ]

        station_codes = [
            item.station_code
            for item in selected_stations
        ]

        database_stations = {
            station.code: station
            for station in PluviometricStation.objects.filter(
                code__in=station_codes
            )
        }

        if len(database_stations) != len(station_codes):
            raise ValidationError(
                "Uma ou mais estações utilizadas no cálculo "
                "não estão mais disponíveis no cadastro."
            )

        records = []

        for item in selected_stations:
            station = database_stations[item.station_code]

            record = MowingWorkloadCalculationStation(
                calculation=calculation,
                station=station,
                sequence=item.sequence,
                distance_km=item.distance_km,
                weight=item.weight,
                weighted_nere=item.weighted_nere,
                station_code_snapshot=item.station_code,
                station_name_snapshot=item.station_name,
                latitude_snapshot=item.latitude,
                longitude_snapshot=item.longitude,
                nere_snapshot=item.nere,
                nd_snapshot=station.nd,
            )

            record.full_clean()
            records.append(record)

        MowingWorkloadCalculationStation.objects.bulk_create(
            records
        )

        return calculation