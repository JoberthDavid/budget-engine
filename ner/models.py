from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PluviometricStation(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
    )

    name = models.CharField(
        max_length=200,
    )

    municipality = models.CharField(
        max_length=150,
    )

    state = models.CharField(
        max_length=2,
    )

    operator = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )

    nd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
    )

    nere = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ],
    )

    norm_reference = models.CharField(
        max_length=100,
        default="DNIT 182/2018 - PRO",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "pluviometric_stations"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class MowingWorkloadLocation(models.Model):
    name = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )

    description = models.TextField(
        blank=True,
        default="",
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "mowing_workload_locations"
        ordering = ["name", "id"]

    def __str__(self):
        return self.name or (
            f"{self.latitude}, {self.longitude}"
        )


class MowingWorkloadCalculation(models.Model):

    class CalculationMethod(models.TextChoices):
        INVERSE_DISTANCE = (
            "INVERSE_DISTANCE",
            "Ponderação pelo inverso da distância",
        )

    location = models.ForeignKey(
        MowingWorkloadLocation,
        on_delete=models.PROTECT,
        related_name="calculations",
    )

    station_count = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(2),
            MaxValueValidator(5),
        ],
    )

    calculation_method = models.CharField(
        max_length=30,
        choices=CalculationMethod.choices,
        default=CalculationMethod.INVERSE_DISTANCE,
    )

    # Média ponderada decimal calculada pelo Angular.
    weighted_nere = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    # NERP inteiro, obtido pelo arredondamento de weighted_nere.
    nerp = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    adjustment = models.SmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(-1),
            MaxValueValidator(1),
        ],
    )

    # Resultado final após aplicação do ajuste.
    ner = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    # Memória de cálculo.
    sum_weighted_nere = models.DecimalField(
        max_digits=20,
        decimal_places=12,
        validators=[
            MinValueValidator(0),
        ],
    )

    sum_weights = models.DecimalField(
        max_digits=20,
        decimal_places=12,
        validators=[
            MinValueValidator(0),
        ],
    )

    norm_reference = models.CharField(
        max_length=100,
        default="DNIT 182/2018 - PRO",
    )

    calculated_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "mowing_workload_calculations"
        ordering = ["-calculated_at"]

    def clean(self):
        super().clean()

        errors = {}

        if self.sum_weights is not None and self.sum_weights <= 0:
            errors["sum_weights"] = (
                "A soma dos pesos deve ser maior que zero."
            )

        if self.weighted_nere is not None and self.nerp is not None:

            expected_nerp = int(
                Decimal(self.weighted_nere).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP,
                )
            )

            if self.nerp != expected_nerp:
                errors["nerp"] = (
                    "O NERP deve corresponder ao arredondamento "
                    "do resultado da média ponderada."
                )

        if self.nerp is not None and self.adjustment is not None:
            expected_ner = max(
                1,
                min(5, self.nerp + self.adjustment),
            )

            if self.ner is not None and self.ner != expected_ner:
                errors["ner"] = (
                    "O NER deve corresponder ao NERP somado ao ajuste, "
                    "limitado ao intervalo de 1 a 5."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"NER {self.ner} - "
            f"{self.location} - "
            f"{self.calculated_at}"
        )


class MowingWorkloadCalculationStation(models.Model):

    calculation = models.ForeignKey(
        MowingWorkloadCalculation,
        on_delete=models.CASCADE,
        related_name="stations",
    )

    station = models.ForeignKey(
        PluviometricStation,
        on_delete=models.PROTECT,
        related_name="calculation_records",
    )

    sequence = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    distance_km = models.DecimalField(
        max_digits=14,
        decimal_places=6,
        validators=[
            MinValueValidator(0),
        ],
    )

    weight = models.DecimalField(
        max_digits=20,
        decimal_places=12,
        validators=[
            MinValueValidator(0),
        ],
    )

    weighted_nere = models.DecimalField(
        max_digits=20,
        decimal_places=12,
        validators=[
            MinValueValidator(0),
        ],
    )

    # Snapshot dos dados normativos utilizados no cálculo.

    station_code_snapshot = models.CharField(
        max_length=20,
    )

    station_name_snapshot = models.CharField(
        max_length=200,
    )

    latitude_snapshot = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude_snapshot = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    nere_snapshot = models.DecimalField(
        max_digits=4,
        decimal_places=2,
    )

    nd_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "mowing_workload_calculation_stations"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["calculation", "station"],
                name="unique_calculation_station",
            ),
            models.UniqueConstraint(
                fields=["calculation", "sequence"],
                name="unique_calculation_station_sequence",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.calculation_id is not None
            and self.sequence is not None
            and self.calculation.station_count is not None
            and self.sequence > self.calculation.station_count
        ):
            raise ValidationError({
                "sequence": (
                    "A sequência não pode exceder a quantidade "
                    "de estações do cálculo."
                )
            })

    def __str__(self):
        return (
            f"{self.calculation_id} - "
            f"{self.station_code_snapshot}"
        )
    

class BudgetMowingWorkload(models.Model):

    budget = models.OneToOneField(
        "app.Budget",
        on_delete=models.PROTECT,
        related_name="mowing_workload",
    )

    location = models.ForeignKey(
        MowingWorkloadLocation,
        on_delete=models.PROTECT,
        related_name="budgets",
    )

    calculation = models.ForeignKey(
        MowingWorkloadCalculation,
        on_delete=models.PROTECT,
        related_name="budget_associations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "budget_mowing_workloads"

    def clean(self):
        super().clean()

        if (
            self.location_id is not None
            and self.calculation_id is not None
            and self.calculation.location_id != self.location_id
        ):
            raise ValidationError({
                "calculation": (
                    "O cálculo informado não pertence "
                    "à localização selecionada."
                )
            })

    def __str__(self):
        return (
            f"Budget {self.budget_id} - "
            f"NER {self.calculation.ner}"
        )
