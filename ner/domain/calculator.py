from dataclasses import dataclass
from decimal import (
    Decimal,
    ROUND_HALF_UP,
    localcontext,
)
from math import (
    atan2,
    cos,
    radians,
    sin,
    sqrt,
)
from typing import Iterable

from ner.domain.exceptions import (
    InsufficientStationsError,
    InvalidNERInputError,
)


ZERO = Decimal("0")
ONE = Decimal("1")

DISTANCE_PRECISION = Decimal("0.000001")
WEIGHT_PRECISION = Decimal("0.000000000001")

MIN_NER = 1
MAX_NER = 5

MIN_STATIONS = 2
MAX_STATIONS = 5

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class PluviometricStationInput:
    """
    Representação mínima de uma estação para o cálculo.

    Não depende do model PluviometricStation.
    """

    code: str
    name: str
    municipality: str
    state: str
    latitude: Decimal
    longitude: Decimal
    nere: Decimal


@dataclass(frozen=True)
class StationCalculationResult:
    """
    Resultado individual de uma estação.
    """

    sequence: int

    station_code: str
    station_name: str
    municipality: str
    state: str

    latitude: Decimal
    longitude: Decimal

    nere: Decimal

    distance_km: Decimal
    weight: Decimal
    weighted_nere: Decimal

    considered: bool


@dataclass(frozen=True)
class NERCalculationResult:
    """
    Resultado completo do cálculo de NER.
    """

    latitude: Decimal
    longitude: Decimal

    station_count: int
    adjustment: int

    calculation_method: str

    sum_weighted_nere: Decimal
    sum_weights: Decimal

    weighted_nere: Decimal
    nerp: int
    ner: int

    stations: tuple[StationCalculationResult, ...]


class NERCalculator:
    """
    Calculador matemático do Nível de Esforço de Roçada.

    Responsabilidades:
    - validar os parâmetros;
    - calcular distâncias;
    - ordenar estações;
    - selecionar estações;
    - calcular pesos;
    - calcular NERE ponderado;
    - determinar NERP;
    - aplicar ajuste técnico;
    - produzir memória de cálculo.
    """

    CALCULATION_METHOD = "INVERSE_DISTANCE"

    def calculate(
        self,
        latitude: Decimal,
        longitude: Decimal,
        stations: Iterable[PluviometricStationInput],
        station_count: int = 5,
        adjustment: int = 0,
    ) -> NERCalculationResult:

        latitude = self._to_decimal(latitude)
        longitude = self._to_decimal(longitude)

        self._validate_coordinates(
            latitude,
            longitude,
        )

        self._validate_parameters(
            station_count,
            adjustment,
        )

        stations = tuple(stations)

        self._validate_stations(stations)

        if len(stations) < station_count:
            raise InsufficientStationsError(
                f"Foram solicitadas {station_count} estações, "
                f"mas existem apenas {len(stations)} disponíveis."
            )

        with localcontext() as context:

            context.prec = 28

            ordered_with_distances = [
                (
                    station,
                    self._calculate_distance_km(
                        latitude,
                        longitude,
                        station.latitude,
                        station.longitude,
                    ),
                )
                for station in stations
            ]

            ordered_with_distances.sort(
                key=lambda item: (item[1], item[0].code)
            )
            # Seleciona as estações mais próximas.
            selected = ordered_with_distances[:station_count]

            # Calcula os pesos das estações selecionadas.
            selected_weights = self._calculate_weights(
                [distance for _, distance in selected]
            )

            # Associa cada estação ao respectivo peso.
            selected_by_code = {
                station.code: weight
                for (station, _), weight in zip(
                    selected,
                    selected_weights,
                )
            }

            # Inicializa os acumuladores.
            sum_weights = ZERO
            sum_weighted_nere = ZERO

            station_results = []

            # Produz os resultados de todas as estações,
            # identificando quais foram efetivamente consideradas.
            for index, (station, distance) in enumerate(
                ordered_with_distances,
                start=1,
            ):
                considered = station.code in selected_by_code

                weight = selected_by_code.get(
                    station.code,
                    ZERO,
                )

                weighted_station_nere = (
                    station.nere * weight
                ).quantize(
                    WEIGHT_PRECISION,
                    rounding=ROUND_HALF_UP,
                )

                if considered:
                    sum_weights += weight
                    sum_weighted_nere += weighted_station_nere

                station_results.append(
                    StationCalculationResult(
                        sequence=index,
                        station_code=station.code,
                        station_name=station.name,
                        municipality=station.municipality,
                        state=station.state,
                        latitude=station.latitude,
                        longitude=station.longitude,
                        nere=station.nere,
                        distance_km=distance,
                        weight=weight,
                        weighted_nere=weighted_station_nere,
                        considered=considered,
                    )
                )
            weighted_nere = (
                sum_weighted_nere / sum_weights
            )

            weighted_nere = weighted_nere.quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )

            nerp = int(
                weighted_nere.quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )

            ner = max(
                MIN_NER,
                min(
                    MAX_NER,
                    nerp + adjustment,
                ),
            )

            return NERCalculationResult(
                latitude=latitude,
                longitude=longitude,
                station_count=station_count,
                adjustment=adjustment,
                calculation_method=self.CALCULATION_METHOD,
                sum_weighted_nere=sum_weighted_nere.quantize(
                    WEIGHT_PRECISION,
                    rounding=ROUND_HALF_UP,
                ),
                sum_weights=sum_weights.quantize(
                    WEIGHT_PRECISION,
                    rounding=ROUND_HALF_UP,
                ),
                weighted_nere=weighted_nere,
                nerp=nerp,
                ner=ner,
                stations=tuple(station_results),
            )

    @staticmethod
    def _to_decimal(value) -> Decimal:

        try:
            return Decimal(str(value))

        except Exception as exc:
            raise InvalidNERInputError(
                f"Valor numérico inválido: {value!r}"
            ) from exc

    def _validate_coordinates(
        self,
        latitude: Decimal,
        longitude: Decimal,
    ) -> None:

        if not latitude.is_finite():
            raise InvalidNERInputError(
                "Latitude deve ser um número finito."
            )

        if not longitude.is_finite():
            raise InvalidNERInputError(
                "Longitude deve ser um número finito."
            )

        if not Decimal("-90") <= latitude <= Decimal("90"):
            raise InvalidNERInputError(
                "Latitude deve estar entre -90 e 90."
            )

        if not Decimal("-180") <= longitude <= Decimal("180"):
            raise InvalidNERInputError(
                "Longitude deve estar entre -180 e 180."
            )

    @staticmethod
    def _validate_parameters(
        station_count: int,
        adjustment: int,
    ) -> None:

        if isinstance(station_count, bool) or not isinstance(
            station_count,
            int,
        ):
            raise InvalidNERInputError(
                "A quantidade de estações deve ser um inteiro."
            )

        if not MIN_STATIONS <= station_count <= MAX_STATIONS:
            raise InvalidNERInputError(
                "A quantidade de estações deve estar entre 2 e 5."
            )

        if isinstance(adjustment, bool) or not isinstance(
            adjustment,
            int,
        ):
            raise InvalidNERInputError(
                "O ajuste técnico deve ser um inteiro."
            )

        if adjustment not in (-1, 0, 1):
            raise InvalidNERInputError(
                "O ajuste técnico deve ser -1, 0 ou 1."
            )

    def _validate_stations(
        self,
        stations: tuple[PluviometricStationInput, ...],
    ) -> None:

        if not stations:
            raise InsufficientStationsError(
                "Não existem estações pluviométricas disponíveis."
            )

        codes = set()

        for station in stations:

            if not station.code:
                raise InvalidNERInputError(
                    "Existe estação sem código."
                )

            if station.code in codes:
                raise InvalidNERInputError(
                    f"Código de estação duplicado: {station.code}."
                )

            codes.add(station.code)

            self._validate_coordinates(
                station.latitude,
                station.longitude,
            )

            if not station.nere.is_finite():
                raise InvalidNERInputError(
                    f"NERE inválido na estação {station.code}."
                )

            if not Decimal("1") <= station.nere <= Decimal("12"):
                raise InvalidNERInputError(
                    f"NERE fora do intervalo de 1 a 12 "
                    f"na estação {station.code}."
                )

    def _calculate_distance_km(
        self,
        latitude_1: Decimal,
        longitude_1: Decimal,
        latitude_2: Decimal,
        longitude_2: Decimal,
    ) -> Decimal:

        lat1 = radians(float(latitude_1))
        lon1 = radians(float(longitude_1))

        lat2 = radians(float(latitude_2))
        lon2 = radians(float(longitude_2))

        delta_latitude = lat2 - lat1
        delta_longitude = lon2 - lon1

        a = (
            sin(delta_latitude / 2) ** 2
            +
            cos(lat1)
            * cos(lat2)
            * sin(delta_longitude / 2) ** 2
        )

        # Proteção contra pequenos erros de ponto flutuante.
        a = max(0.0, min(1.0, a))

        c = 2 * atan2(
            sqrt(a),
            sqrt(1.0 - a),
        )

        distance = EARTH_RADIUS_KM * c

        return Decimal(str(distance)).quantize(
            DISTANCE_PRECISION,
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _calculate_weights(
        distances: list[Decimal],
    ) -> list[Decimal]:

        coincident = [
            distance == ZERO
            for distance in distances
        ]

        if any(coincident):

            # Se houver coincidência geográfica,
            # somente as estações coincidentes
            # recebem peso, igualmente distribuído.

            return [
                (
                    ONE / Decimal(sum(coincident))
                    if is_coincident
                    else ZERO
                ).quantize(
                    WEIGHT_PRECISION,
                    rounding=ROUND_HALF_UP,
                )
                for is_coincident in coincident
            ]

        return [
            (ONE / distance).quantize(
                WEIGHT_PRECISION,
                rounding=ROUND_HALF_UP,
            )
            for distance in distances
        ]