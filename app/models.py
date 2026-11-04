from django.core.exceptions import ValidationError
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

    def __str__(self) -> str:
        return self.name


class BDIQuota(models.Model):
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