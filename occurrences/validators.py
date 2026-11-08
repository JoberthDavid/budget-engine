import re

from django.core.exceptions import ValidationError


BRAZILIAN_STATES = [
    ("AC", "Acre"),
    ("AL", "Alagoas"),
    ("AP", "Amapá"),
    ("AM", "Amazonas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"),
    ("GO", "Goiás"),
    ("MA", "Maranhão"),
    ("MT", "Mato Grosso"),
    ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"),
    ("PA", "Pará"),
    ("PB", "Paraíba"),
    ("PR", "Paraná"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RJ", "Rio de Janeiro"),
    ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"),
    ("RO", "Rondônia"),
    ("RR", "Roraima"),
    ("SC", "Santa Catarina"),
    ("SP", "São Paulo"),
    ("SE", "Sergipe"),
    ("TO", "Tocantins"),
]


def normalize_cnpj(value):
    if not value:
        return None

    value = str(value).strip()

    if not re.fullmatch(r"[0-9./\-\s]+", value):
        raise ValidationError("O CNPJ contém caracteres inválidos.")

    digits = re.sub(r"\D", "", value)

    if len(digits) != 14:
        raise ValidationError("O CNPJ deve conter 14 dígitos.")

    if digits == digits[0] * 14:
        raise ValidationError("CNPJ inválido.")

    def calculate_digit(number, weights):
        total = sum(
            int(digit) * weight
            for digit, weight in zip(number, weights)
        )
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_digit = calculate_digit(
        digits[:12],
        [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    )

    second_digit = calculate_digit(
        digits[:12] + first_digit,
        [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
    )

    if digits[-2:] != first_digit + second_digit:
        raise ValidationError("Os dígitos verificadores do CNPJ são inválidos.")

    return digits


def normalize_postal_code(value):
    if not value:
        return ""

    value = str(value).strip()

    if not re.fullmatch(r"\d{5}-?\d{3}", value):
        raise ValidationError(
            "O CEP deve conter oito dígitos, com ou sem hífen."
        )

    return value.replace("-", "")


def normalize_state(value):
    if not value:
        return value

    state = str(value).strip().upper()

    valid_states = {code for code, _ in BRAZILIAN_STATES}

    if state not in valid_states:
        raise ValidationError("Informe uma UF brasileira válida.")

    return state