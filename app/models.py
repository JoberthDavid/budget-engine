from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Project(models.Model):
    name = models.CharField(
        max_length=200,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "projects"

    def __str__(self):
        return self.name


class Budget(models.Model):

    class Methodology(models.TextChoices):
        SC = "SC", "SICRO"
        SN = "SN", "SINAPI"

    class TypeSystem(models.TextChoices):
        ON = "ON", "Onerado"
        DS = "DS", "Desonerado"
        NA = "NA", "Não aplicável"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        ACTIVE = "ACTIVE", "Ativo"
        FINALIZED = "FINALIZED", "Finalizado"

    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="budgets",
    )

    source_file_uf = models.CharField(
        max_length=2,
    )

    methodology = models.CharField(
        max_length=2,
        choices=Methodology.choices,
    )

    type_system = models.CharField(
        max_length=2,
        choices=TypeSystem.choices,
    )

    monetary_base_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "budgets"

    def __str__(self):
        return f"Budget {self.pk}"


class BudgetDomain(models.Model):

    budget = models.ForeignKey(
        Budget,
        on_delete=models.PROTECT,
        related_name="budget_domains",
    )

    highway = models.CharField(
        max_length=50,
        blank=True,
    )

    initial_km = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )

    final_km = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )

    snv = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "budget_domains"

    def __str__(self):
        return f"{self.highway} - KM {self.initial_km} ao KM {self.final_km}"


class BDIMethod(models.Model):
    method = models.CharField(
        max_length=100,
        unique=True,
    )

    def __str__(self) -> str:
        return self.method


class BDI(models.Model):
    name = models.CharField(
        max_length=150,
    )

    slug = models.SlugField(
        max_length=150,
        unique=True,
    )

    method = models.ForeignKey(
        BDIMethod,
        on_delete=models.PROTECT,
        related_name="bdis",
    )

    observation = models.TextField(
        blank=True,
        default="",
    )

    def __str__(self) -> str:
        return self.name


class BDIQuota(models.Model):

    class Base(models.TextChoices):
        CD = "CD", "Custo Direto"
        PV = "PV", "Preço de Venda"

    bdi = models.ForeignKey(
        BDI,
        on_delete=models.CASCADE,
        related_name="quotas",
    )

    group = models.CharField(
        max_length=100,
    )

    description = models.CharField(
        max_length=200,
    )

    percentage = models.DecimalField(
        max_digits=12,
        decimal_places=6,
    )

    variable = models.CharField(
        max_length=100,
    )

    base = models.CharField(
        max_length=2,
        choices=Base.choices,
    )

    def __str__(self) -> str:
        return f"{self.bdi.name} - {self.description}"


class BudgetBDI(models.Model):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.PROTECT,
        related_name="budget_bdis",
    )

    bdi = models.ForeignKey(
        BDI,
        on_delete=models.PROTECT,
        related_name="budget_bdis",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "budget_bdis"
        constraints = [
            models.UniqueConstraint(
                fields=["budget", "bdi"],
                name="unique_budget_bdi",
            ),
        ]

    def __str__(self):
        return f"{self.budget_id} - {self.bdi.name}"


class BudgetService(models.Model):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.PROTECT,
        related_name="services",
    )

    label = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=True,
    )

    code = models.CharField(
        max_length=100,
    )

    description = models.CharField(
        max_length=500,
    )

    unit = models.CharField(
        max_length=50,
    )

    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=6,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "budget_services"
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(
                fields=["budget", "label"],
                name="unique_budget_service_label",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.label is None:
            last_label = (
                BudgetService.objects
                .filter(budget=self.budget)
                .aggregate(max_label=models.Max("label"))
                ["max_label"]
            )

            self.label = (last_label or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} - {self.code} - {self.description}"


class BudgetComposition(models.Model):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.PROTECT,
        related_name="compositions",
    )

    service = models.ForeignKey(
        BudgetService,
        on_delete=models.PROTECT,
        related_name="compositions",
    )

    budget_bdi = models.ForeignKey(
        BudgetBDI,
        on_delete=models.PROTECT,
        related_name="compositions",
    )

    label = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=True,
    )

    composition_id = models.CharField(
        max_length=100,
    )

    reference_base_date = models.DateField()

    factor = models.DecimalField(
        max_digits=20,
        decimal_places=6,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "budget_compositions"
        ordering = ["label"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "label"],
                name="unique_service_composition_label",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if self.service_id is not None:
            if self.budget_id is not None:
                if self.service.budget_id != self.budget_id:
                    errors["service"] = (
                        "O serviço deve pertencer ao mesmo orçamento "
                        "da composição."
                    )

            if self.budget_bdi_id is not None:
                if self.budget_bdi.budget_id != self.service.budget_id:
                    errors["budget_bdi"] = (
                        "O BDI deve pertencer ao mesmo orçamento "
                        "do serviço."
                    )

        if self.budget_bdi_id is not None:
            if self.budget_id is not None:
                if self.budget_bdi.budget_id != self.budget_id:
                    errors["budget_bdi"] = (
                        "O BDI deve pertencer ao mesmo orçamento "
                        "da composição."
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.label is None:
            last_label = (
                BudgetComposition.objects
                .filter(service=self.service)
                .aggregate(max_label=models.Max("label"))
                ["max_label"]
            )

            self.label = (last_label or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} - {self.composition_id}"


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
        Budget,
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