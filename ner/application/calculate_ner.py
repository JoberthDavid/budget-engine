from decimal import Decimal

from ner.domain.calculator import (
    NERCalculator,
    PluviometricStationInput,
)
from ner.models import PluviometricStation


class CalculateNERService:
    """
    Serviço de aplicação responsável por:
    - consultar as estações pluviométricas;
    - converter os modelos em objetos do domínio;
    - executar a calculadora NER.
    """

    def __init__(self, calculator=None):
        self.calculator = calculator or NERCalculator()

    def execute(
        self,
        latitude,
        longitude,
        station_count=5,
        adjustment=0,
    ):
        stations = PluviometricStation.objects.all().order_by("code")

        station_inputs = [
            PluviometricStationInput(
                code=station.code,
                name=station.name,
                municipality=station.municipality,
                state=station.state,
                latitude=Decimal(station.latitude),
                longitude=Decimal(station.longitude),
                nere=Decimal(station.nere),
            )
            for station in stations
        ]

        return self.calculator.calculate(
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            stations=station_inputs,
            station_count=station_count,
            adjustment=adjustment,
        )