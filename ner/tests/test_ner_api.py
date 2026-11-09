from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from ner.models import PluviometricStation
from types import SimpleNamespace


class NERStationAPITestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=SimpleNamespace(
                is_authenticated=True,
                is_anonymous=False,
                username="user:test",
            ),
            token={
                "sub": "user:test",
                "scope": ["ner:stations:read"],
            },
        )

        self.station_1 = PluviometricStation.objects.create(
            code="1547004",
            name="Brasília",
            municipality="Brasília",
            state="DF",
            operator="INMET",
            latitude=Decimal("-15.790000"),
            longitude=Decimal("-47.922778"),
            nd=Decimal("0.025430"),
            nere=Decimal("4.30"),
            norm_reference="DNIT 182/2018 - PRO",
        )

        self.station_2 = PluviometricStation.objects.create(
            code="1549001",
            name="Goianésia",
            municipality="Goianésia",
            state="GO",
            operator="CPRM",
            latitude=Decimal("-15.329167"),
            longitude=Decimal("-49.121667"),
            nd=Decimal("0.026320"),
            nere=Decimal("4.40"),
            norm_reference="DNIT 182/2018 - PRO",
        )

        self.station_3 = PluviometricStation.objects.create(
            code="1750001",
            name="Fazenda do Turno",
            municipality="Paraúna",
            state="GO",
            operator="CPRM",
            latitude=Decimal("-17.079167"),
            longitude=Decimal("-50.289444"),
            nd=Decimal("0.025200"),
            nere=Decimal("4.30"),
            norm_reference="DNIT 182/2018 - PRO",
        )

    def test_list_stations_returns_all_stations(self):
        response = self.client.get("/ner/stations")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 3)

    def test_list_stations_returns_expected_fields(self):
        response = self.client.get("/ner/stations")

        self.assertEqual(response.status_code, 200)

        station = response.json()[0]

        expected_fields = {
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
        }

        self.assertEqual(
            set(station.keys()),
            expected_fields,
        )

    def test_list_stations_orders_by_code(self):
        response = self.client.get("/ner/stations")

        self.assertEqual(response.status_code, 200)

        codes = [
            station["code"]
            for station in response.json()
        ]

        self.assertEqual(
            codes,
            ["1547004", "1549001", "1750001"],
        )

    def test_filter_stations_by_state(self):
        response = self.client.get(
            "/ner/stations?state=GO"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 2)

        self.assertTrue(
            all(station["state"] == "GO" for station in data)
        )

    def test_filter_stations_by_state_is_case_insensitive(self):
        response = self.client.get(
            "/ner/stations?state=go"
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.json()), 2)

    def test_filter_stations_by_municipality(self):
        response = self.client.get(
            "/ner/stations?municipality=Goi"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "1549001")

    def test_filter_stations_by_code(self):
        response = self.client.get(
            "/ner/stations?code=1547004"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Brasília")

    def test_search_stations_by_name(self):
        response = self.client.get(
            "/ner/stations?search=Brasília"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "1547004")

    def test_search_stations_by_code(self):
        response = self.client.get(
            "/ner/stations?search=1549001"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Goianésia")

    def test_search_stations_by_municipality(self):
        response = self.client.get(
            "/ner/stations?search=Paraúna"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "1750001")

    def test_combine_station_filters(self):
        response = self.client.get(
            "/ner/stations?state=GO&search=Goianésia"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "1549001")

    def test_filter_stations_returns_empty_list_when_not_found(self):
        response = self.client.get(
            "/ner/stations?state=XX"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_station_response_contains_decimal_values(self):
        response = self.client.get(
            "/ner/stations?code=1547004"
        )

        self.assertEqual(response.status_code, 200)

        station = response.json()[0]

        self.assertEqual(
            station["latitude"],
            "-15.790000",
        )

        self.assertEqual(
            station["longitude"],
            "-47.922778",
        )

        self.assertEqual(
            station["nere"],
            "4.30",
        )

    def test_post_method_is_not_allowed(self):
        response = self.client.post(
            "/ner/stations",
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_put_method_is_not_allowed(self):
        response = self.client.put(
            "/ner/stations",
            data={},
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_delete_method_is_not_allowed(self):
        response = self.client.delete(
            "/ner/stations"
        )

        self.assertEqual(response.status_code, 405)

        self.assertEqual(
            PluviometricStation.objects.count(),
            3,
        )