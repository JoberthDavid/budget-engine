from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from ner.models import (
    MowingWorkloadCalculation,
    MowingWorkloadCalculationStation,
    MowingWorkloadLocation,
    PluviometricStation,
)


class NERCalculationAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.stations = [
            PluviometricStation.objects.create(
                code=f"ST{i}",
                name=f"Estação {i}",
                municipality="Brasília",
                state="DF",
                operator="INMET",
                latitude=Decimal(f"-15.{i}00000"),
                longitude=Decimal("-47.900000"),
                nd=Decimal("0.025430"),
                nere=Decimal("3.50"),
                norm_reference="DNIT 182/2018 - PRO",
            )
            for i in range(1, 6)
        ]

        self.payload = {
            "latitude": "-15.780000",
            "longitude": "-47.930000",
            "station_count": 5,
            "adjustment": 0,
            "location_name": "Trecho de teste",
            "location_description": "Localização de teste",
        }

    def test_create_calculation_returns_persisted_result(self):
        response = self.client.post(
            "/ner/calculations",
            data=self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertIn("id", data)
        self.assertIn("location", data)
        self.assertIn("stations", data)

        self.assertEqual(data["location"]["name"], "Trecho de teste")
        self.assertEqual(data["station_count"], 5)
        self.assertEqual(data["ner"], 4)
        self.assertEqual(len(data["stations"]), 5)

        self.assertEqual(
            MowingWorkloadCalculation.objects.count(),
            1,
        )

        self.assertEqual(
            MowingWorkloadLocation.objects.count(),
            1,
        )

        self.assertEqual(
            MowingWorkloadCalculationStation.objects.count(),
            5,
        )

    def test_create_calculation_uses_default_parameters(self):
        payload = {
            "latitude": "-15.780000",
            "longitude": "-47.930000",
        }

        response = self.client.post(
            "/ner/calculations",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["station_count"], 5)
        self.assertEqual(data["adjustment"], 0)

    def test_create_calculation_applies_adjustment(self):
        payload = {
            **self.payload,
            "adjustment": 1,
        }

        response = self.client.post(
            "/ner/calculations",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["adjustment"], 1)
        self.assertEqual(data["ner"], 5)

    def test_invalid_latitude_returns_400(self):
        payload = {
            **self.payload,
            "latitude": "-95.000000",
        }

        response = self.client.post(
            "/ner/calculations",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            MowingWorkloadCalculation.objects.count(),
            0,
        )

    def test_invalid_station_count_returns_400(self):
        payload = {
            **self.payload,
            "station_count": 6,
        }

        response = self.client.post(
            "/ner/calculations",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            MowingWorkloadCalculation.objects.count(),
            0,
        )

    def test_insufficient_stations_returns_400_without_persistence(self):
        PluviometricStation.objects.filter(
            code__in=["ST4", "ST5"]
        ).delete()

        response = self.client.post(
            "/ner/calculations",
            data=self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            MowingWorkloadCalculation.objects.count(),
            0,
        )

        self.assertEqual(
            MowingWorkloadLocation.objects.count(),
            0,
        )

    def test_post_method_is_not_allowed_on_station_list(self):
        response = self.client.post(
            "/ner/stations",
            data=self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_calculation_response_contains_station_snapshots(self):
        response = self.client.post(
            "/ner/calculations",
            data=self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        station_data = response.json()["stations"][0]

        expected_fields = {
            "station_id",
            "sequence",
            "station_code",
            "station_name",
            "latitude",
            "longitude",
            "nere",
            "nd",
            "distance_km",
            "weight",
            "weighted_nere",
        }

        self.assertEqual(
            set(station_data.keys()),
            expected_fields,
        )

        self.assertEqual(
            station_data["nere"],
            "3.50",
        )

    def test_station_changes_do_not_modify_calculation_snapshots(self):
        response = self.client.post(
            "/ner/calculations",
            data=self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        calculation = MowingWorkloadCalculation.objects.get(
            pk=response.json()["id"]
        )

        station = self.stations[0]

        record = MowingWorkloadCalculationStation.objects.get(
            calculation=calculation,
            station=station,
        )

        original_name = record.station_name_snapshot
        original_nere = record.nere_snapshot
        original_latitude = record.latitude_snapshot
        original_nd = record.nd_snapshot

        station.name = "Estação alterada"
        station.nere = Decimal("5.50")
        station.latitude = Decimal("-16.000000")
        station.nd = Decimal("0.050000")
        station.save()

        record.refresh_from_db()

        self.assertEqual(
            record.station_name_snapshot,
            original_name,
        )

        self.assertEqual(
            record.nere_snapshot,
            original_nere,
        )

        self.assertEqual(
            record.latitude_snapshot,
            original_latitude,
        )

        self.assertEqual(
            record.nd_snapshot,
            original_nd,
        )