class NERCalculationError(Exception):
    """Erro base do domínio de cálculo do NER."""


class InvalidNERInputError(NERCalculationError):
    """Parâmetros de entrada inválidos."""


class InsufficientStationsError(NERCalculationError):
    """Quantidade insuficiente de estações para o cálculo."""