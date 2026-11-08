from django.db import models


class BDIMethod(models.Model):
    method = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        db_table = "app_bdimethod"

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

    class Meta:
        db_table = "app_bdi"

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

    class Meta:
        db_table = "app_bdiquota"

    def __str__(self) -> str:
        return f"{self.bdi.name} - {self.description}"


class BudgetBDI(models.Model):
    budget = models.ForeignKey(
        "app.Budget",
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