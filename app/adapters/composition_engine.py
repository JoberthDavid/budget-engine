from __future__ import annotations

from app.ports.composition_calculator import CalculatedComposition, CompositionCalculatorPort


class CompositionEngineAdapter(CompositionCalculatorPort):
    """Adaptador para a API Python do composition-engine.

    A integração concreta será fechada após definir o ponto público de entrada
    que o budget-engine usará. Nenhuma dependência Flask é introduzida no engine.
    """

    def calculate(self, **kwargs) -> CalculatedComposition:
        raise NotImplementedError(
            "CompositionEngineAdapter ainda não foi conectado ao composition-engine."
        )
