from decimal import Decimal

from django.test import TestCase

from ner.application.calculate_ner import CalculateNERService
from ner.application.save_ner_calculation import (
    SaveNERCalculationService,
)
from ner.models import (
    MowingWorkloadCalculation,
    MowingWorkloadCalculationStation,
    MowingWorkloadLocation,
    PluviometricStation,
)
from unittest.mock import patch

from ner.application.save_ner_calculation import (
    SaveNERCalculationService,
)


class NERApplicationTestCase(TestCase):

    def setUp(self):
        self.stations = [
            PluviometricStation.objects.create(
                code=f"ST{i}",
                name=f"Estação {i}",
                municipality="Brasília",
                state="DF",
                latitude=Decimal(f"-15.{i}00000"),
                longitude=Decimal("-47.900000"),
                nere=Decimal("3.50"),
            )
            for i in range(1, 6)
        ]

    def test_calculate_ner_uses_registered_stations(self):
        service = CalculateNERService()

        result = service.execute(
            latitude=Decimal("-15.780000"),
            longitude=Decimal("-47.930000"),
            station_count=5,
            adjustment=0,
        )

        self.assertEqual(result.station_count, 5)
        self.assertEqual(len(result.stations), 5)
        self.assertGreaterEqual(result.ner, 1)
        self.assertLessEqual(result.ner, 5)

    def test_save_ner_calculation_persists_calculation_and_stations(self):
        result = CalculateNERService().execute(
            latitude=Decimal("-15.780000"),
            longitude=Decimal("-47.930000"),
            station_count=5,
            adjustment=0,
        )

        calculation = SaveNERCalculationService().execute(
            result=result,
            location_name="Trecho de teste",
            location_description="Teste de persistência",
        )

        self.assertTrue(
            MowingWorkloadCalculation.objects.filter(
                pk=calculation.pk
            ).exists()
        )

        self.assertTrue(
            MowingWorkloadLocation.objects.filter(
                pk=calculation.location_id
            ).exists()
        )

        self.assertEqual(
            MowingWorkloadCalculationStation.objects.filter(
                calculation=calculation
            ).count(),
            5,
        )

    def test_save_preserves_station_snapshots(self):
        result = CalculateNERService().execute(
            latitude=Decimal("-15.780000"),
            longitude=Decimal("-47.930000"),
            station_count=5,
        )

        calculation = SaveNERCalculationService().execute(
            result=result,
        )

        record = calculation.stations.first()

        self.assertEqual(
            record.station_code_snapshot,
            record.station.code,
        )

        self.assertEqual(
            record.nere_snapshot,
            record.station.nere,
        )

    def test_save_calculation_rolls_back_on_station_persistence_failure(self):
        result = CalculateNERService().execute(
            latitude=Decimal("-15.780000"),
            longitude=Decimal("-47.930000"),
            station_count=5,
        )

        with patch.object(
            MowingWorkloadCalculationStation.objects,
            "bulk_create",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                SaveNERCalculationService().execute(
                    result=result,
                    location_name="Teste de rollback",
                )

        self.assertEqual(
            MowingWorkloadLocation.objects.count(),
            0,
        )

        self.assertEqual(
            MowingWorkloadCalculation.objects.count(),
            0,
        )

        self.assertEqual(
            MowingWorkloadCalculationStation.objects.count(),
            0,
        )