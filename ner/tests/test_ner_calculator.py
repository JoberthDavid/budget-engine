from decimal import Decimal

from django.test import SimpleTestCase

from ner.domain.calculator import (
    NERCalculator,
    PluviometricStationInput,
)

from ner.domain.exceptions import (
    InsufficientStationsError,
    InvalidNERInputError,
)


class NERCalculatorTestCase(SimpleTestCase):

    def setUp(self):
        self.calculator = NERCalculator()

        self.latitude = Decimal("-15.790000")
        self.longitude = Decimal("-47.922778")

        self.stations = [
            PluviometricStationInput(
                code="1547004",
                name="Brasília",
                municipality="Brasília",
                state="DF",
                latitude=Decimal("-15.790000"),
                longitude=Decimal("-47.922778"),
                nere=Decimal("4.30"),
            ),
            PluviometricStationInput(
                code="1549001",
                name="Goianésia",
                municipality="Goianésia",
                state="GO",
                latitude=Decimal("-15.329167"),
                longitude=Decimal("-49.121667"),
                nere=Decimal("4.40"),
            ),
            PluviometricStationInput(
                code="1750001",
                name="Fazenda do Turno",
                municipality="Paraúna",
                state="GO",
                latitude=Decimal("-17.079167"),
                longitude=Decimal("-50.289444"),
                nere=Decimal("4.30"),
            ),
            PluviometricStationInput(
                code="1547013",
                name="Taquara",
                municipality="Brasília",
                state="DF",
                latitude=Decimal("-15.632222"),
                longitude=Decimal("-47.520278"),
                nere=Decimal("3.60"),
            ),
            PluviometricStationInput(
                code="1542016",
                name="Serra Branca",
                municipality="Minas Gerais",
                state="MG",
                latitude=Decimal("-15.000000"),
                longitude=Decimal("-44.000000"),
                nere=Decimal("3.10"),
            ),
        ]

    def calculate(self, **overrides):

        parameters = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "stations": self.stations,
            "station_count": 5,
            "adjustment": 0,
        }

        parameters.update(overrides)

        return self.calculator.calculate(**parameters)

    def test_calculation_returns_expected_structure(self):

        result = self.calculate()

        self.assertEqual(result.station_count, 5)

        self.assertEqual(len(result.stations), 5)

        self.assertEqual(
            result.calculation_method,
            "INVERSE_DISTANCE",
        )

        self.assertGreater(result.sum_weights, Decimal("0"))

        self.assertGreater(
            result.sum_weighted_nere,
            Decimal("0"),
        )

        self.assertGreater(
            result.weighted_nere,
            Decimal("0"),
        )

    def test_stations_are_ordered_by_distance(self):

        result = self.calculate()

        distances = [
            station.distance_km
            for station in result.stations
        ]

        self.assertEqual(
            distances,
            sorted(distances),
        )

    def test_station_count_selects_nearest_stations(self):

        result = self.calculate(
            station_count=2,
        )

        self.assertEqual(len(result.stations), 5)

        considered = [
            station
            for station in result.stations
            if station.considered
        ]

        self.assertEqual(len(considered), 2)

        self.assertEqual(
            considered[0].station_code,
            "1547004",
        )

    def test_station_sequence_starts_at_one(self):

        result = self.calculate()

        sequences = [
            station.sequence
            for station in result.stations
        ]

        self.assertEqual(
            sequences,
            [1, 2, 3, 4, 5],
        )

    def test_calculation_uses_inverse_distance_weights(self):

        result = self.calculate(
            station_count=2,
        )

        first = result.stations[0]
        second = result.stations[1]

        self.assertGreater(
            first.weight,
            second.weight,
        )

    def test_weighted_nere_is_consistent_with_memory(self):

        result = self.calculate()

        expected = (
            result.sum_weighted_nere
            / result.sum_weights
        ).quantize(
            Decimal("0.000001")
        )

        self.assertEqual(
            result.weighted_nere,
            expected,
        )

    def test_nerp_uses_half_up_rounding(self):

        result = self.calculate(
            stations=[
                PluviometricStationInput(
                    code="A",
                    name="Estação A",
                    municipality="Teste",
                    state="GO",
                    latitude=Decimal("-15.790000"),
                    longitude=Decimal("-47.922778"),
                    nere=Decimal("3.50"),
                ),
                PluviometricStationInput(
                    code="B",
                    name="Estação B",
                    municipality="Teste",
                    state="GO",
                    latitude=Decimal("-15.790000"),
                    longitude=Decimal("-47.922778"),
                    nere=Decimal("3.50"),
                ),
            ],
            station_count=2,
        )

        self.assertEqual(
            result.weighted_nere,
            Decimal("3.500000"),
        )

        self.assertEqual(
            result.nerp,
            4,
        )

    def test_adjustment_is_applied_to_nerp(self):

        result = self.calculate(
            adjustment=1,
        )

        self.assertEqual(
            result.ner,
            min(5, result.nerp + 1),
        )

    def test_negative_adjustment_is_applied(self):

        result = self.calculate(
            adjustment=-1,
        )

        self.assertEqual(
            result.ner,
            max(1, min(5, result.nerp - 1)),
        )

    def test_ner_is_limited_to_five(self):

        result = self.calculate(
            stations=[
                PluviometricStationInput(
                    code="A",
                    name="Estação A",
                    municipality="Teste",
                    state="GO",
                    latitude=Decimal("-15.790000"),
                    longitude=Decimal("-47.922778"),
                    nere=Decimal("5.00"),
                ),
                PluviometricStationInput(
                    code="B",
                    name="Estação B",
                    municipality="Teste",
                    state="GO",
                    latitude=Decimal("-15.790000"),
                    longitude=Decimal("-47.922778"),
                    nere=Decimal("5.00"),
                ),
            ],
            station_count=2,
            adjustment=1,
        )

        self.assertEqual(result.ner, 5)

    def test_zero_distance_does_not_generate_artificial_weight(self):

        result = self.calculate(
            station_count=2,
        )

        coincident = [
            station
            for station in result.stations
            if station.distance_km == Decimal("0")
        ]

        self.assertEqual(len(coincident), 1)

        self.assertEqual(
            coincident[0].weight,
            Decimal("1.000000000000"),
        )

        self.assertEqual(
            result.sum_weights,
            Decimal("1.000000000000"),
        )

    def test_multiple_coincident_stations_share_weight(self):

        stations = [
            PluviometricStationInput(
                code="A",
                name="Estação A",
                municipality="Teste",
                state="GO",
                latitude=self.latitude,
                longitude=self.longitude,
                nere=Decimal("3.00"),
            ),
            PluviometricStationInput(
                code="B",
                name="Estação B",
                municipality="Teste",
                state="GO",
                latitude=self.latitude,
                longitude=self.longitude,
                nere=Decimal("5.00"),
            ),
        ]

        result = self.calculate(
            stations=stations,
            station_count=2,
        )

        self.assertEqual(
            result.weighted_nere,
            Decimal("4.000000"),
        )

        self.assertEqual(result.nerp, 4)

    def test_insufficient_stations_raises_error(self):

        with self.assertRaises(InsufficientStationsError):
            self.calculate(
                stations=self.stations[:3],
                station_count=5,
            )

    def test_invalid_station_count_raises_error(self):

        with self.assertRaises(InvalidNERInputError):
            self.calculate(
                station_count=1,
            )

    def test_invalid_adjustment_raises_error(self):

        with self.assertRaises(InvalidNERInputError):
            self.calculate(
                adjustment=2,
            )

    def test_invalid_latitude_raises_error(self):

        with self.assertRaises(InvalidNERInputError):
            self.calculate(
                latitude=Decimal("91"),
            )

    def test_invalid_longitude_raises_error(self):

        with self.assertRaises(InvalidNERInputError):
            self.calculate(
                longitude=Decimal("181"),
            )

    def test_invalid_station_nere_raises_error(self):

        invalid_stations = [
            PluviometricStationInput(
                code="A",
                name="Estação A",
                municipality="Teste",
                state="GO",
                latitude=Decimal("-15.790000"),
                longitude=Decimal("-47.922778"),
                nere=Decimal("13.00"),
            ),
            PluviometricStationInput(
                code="B",
                name="Estação B",
                municipality="Teste",
                state="GO",
                latitude=Decimal("-15.800000"),
                longitude=Decimal("-47.930000"),
                nere=Decimal("4.00"),
            ),
        ]

        with self.assertRaises(InvalidNERInputError):
            self.calculate(
                stations=invalid_stations,
                station_count=2,
            )

    def test_duplicate_station_codes_are_rejected(self):

        stations = [
            self.stations[0],
            PluviometricStationInput(
                code=self.stations[0].code,
                name="Outra estação",
                municipality="Teste",
                state="GO",
                latitude=Decimal("-15.800000"),
                longitude=Decimal("-47.930000"),
                nere=Decimal("4.00"),
            ),
        ]

        with self.assertRaises(InvalidNERInputError):
            self.calculate(
                stations=stations,
                station_count=2,
            )

    def test_tied_distances_are_ordered_by_station_code(self):

        stations = [
            PluviometricStationInput(
                code="B",
                name="Estação B",
                municipality="Teste",
                state="GO",
                latitude=Decimal("-15.800000"),
                longitude=Decimal("-47.930000"),
                nere=Decimal("4.00"),
            ),
            PluviometricStationInput(
                code="A",
                name="Estação A",
                municipality="Teste",
                state="GO",
                latitude=Decimal("-15.800000"),
                longitude=Decimal("-47.930000"),
                nere=Decimal("4.00"),
            ),
        ]

        result = self.calculate(
            stations=stations,
            station_count=2,
        )

        self.assertEqual(
            [
                station.station_code
                for station in result.stations
            ],
            ["A", "B"],
        )