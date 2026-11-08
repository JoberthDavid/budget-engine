from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q

from app.models import Budget
from occurrences.models import (
    Material,
    SupplierLocation,
    SupplierLocationMaterial,
)


class SupplierQuotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        VALID = "VALID", "Válida"
        EXPIRED = "EXPIRED", "Expirada"
        CANCELLED = "CANCELLED", "Cancelada"

    supplier_location = models.ForeignKey(
        SupplierLocation,
        on_delete=models.PROTECT,
        related_name="quotations",
    )

    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="quotations",
    )

    quoted_at = models.DateField()
    valid_until = models.DateField(null=True, blank=True)

    unit_price = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("0.000001"))],
    )
    unit = models.CharField(max_length=30)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    source_document = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "supplier_quotations"
        ordering = ["-quoted_at", "-id"]
        indexes = [
            models.Index(
                fields=["material", "quoted_at"],
                name="quotation_material_date_idx",
            ),
            models.Index(
                fields=["supplier_location", "quoted_at"],
                name="quotation_location_date_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(unit_price__gt=0),
                name="quotation_unit_price_positive",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if (
            self.valid_until
            and self.quoted_at
            and self.valid_until < self.quoted_at
        ):
            errors["valid_until"] = (
                "A validade não pode anteceder a data da cotação."
            )

        if (
            self.supplier_location_id
            and self.material_id
            and not SupplierLocationMaterial.objects.filter(
                supplier_location_id=self.supplier_location_id,
                material_id=self.material_id,
                active=True,
            ).exists()
        ):
            errors["material"] = (
                "O material não está cadastrado como ofertado "
                "por este estabelecimento."
            )

        if self.pk and self.status != self.Status.VALID:
            if self.budget_links.exists():
                errors["status"] = (
                    "Uma cotação associada a orçamento não pode "
                    "ser expirada ou cancelada."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                # Serializa alterações concorrentes sobre a cotação.
                type(self).objects.select_for_update().get(pk=self.pk)

            self.full_clean()
            super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.material} - "
            f"{self.supplier_location} - "
            f"{self.quoted_at}"
        )


class BudgetQuotation(models.Model):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.PROTECT,
        related_name="quotation_links",
    )
    quotation = models.ForeignKey(
        SupplierQuotation,
        on_delete=models.PROTECT,
        related_name="budget_links",
    )

    # Snapshot comercial e documental.
    supplier_name_snapshot = models.CharField(max_length=200)
    supplier_cnpj_snapshot = models.CharField(
        max_length=14,
        blank=True,
        default="",
    )

    location_name_snapshot = models.CharField(max_length=200)
    street_snapshot = models.CharField(max_length=200, blank=True, default="")
    number_snapshot = models.CharField(max_length=30, blank=True, default="")
    complement_snapshot = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    municipality_snapshot = models.CharField(max_length=150, blank=True, default="")
    state_snapshot = models.CharField(max_length=2, blank=True, default="")
    postal_code_snapshot = models.CharField(max_length=8, blank=True, default="")

    material_code_snapshot = models.CharField(max_length=50)
    material_description_snapshot = models.CharField(max_length=250)

    quoted_at_snapshot = models.DateField()
    valid_until_snapshot = models.DateField(null=True, blank=True)
    unit_price_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
    )
    unit_snapshot = models.CharField(max_length=30)
    source_document_snapshot = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )

    notes = models.TextField(blank=True, default="")
    associated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "budget_quotations"
        constraints = [
            models.UniqueConstraint(
                fields=["budget", "quotation"],
                name="unique_budget_quotation",
            ),
        ]
        ordering = ["-associated_at"]

    def clean(self):
        super().clean()

        if not self.quotation_id:
            return

        if self.quotation.status != SupplierQuotation.Status.VALID:
            raise ValidationError({
                "quotation": (
                    "Somente cotações válidas podem ser "
                    "associadas a um orçamento."
                )
            })

        if self.pk:
            original = type(self).objects.get(pk=self.pk)

            protected_fields = [
                "budget_id",
                "quotation_id",
                "supplier_name_snapshot",
                "supplier_cnpj_snapshot",
                "location_name_snapshot",
                "street_snapshot",
                "number_snapshot",
                "complement_snapshot",
                "municipality_snapshot",
                "state_snapshot",
                "postal_code_snapshot",
                "material_code_snapshot",
                "material_description_snapshot",
                "quoted_at_snapshot",
                "valid_until_snapshot",
                "unit_price_snapshot",
                "unit_snapshot",
                "source_document_snapshot",
                "associated_at",
            ]

            changed = [
                field
                for field in protected_fields
                if getattr(self, field) != getattr(original, field)
            ]

            if changed:
                raise ValidationError(
                    "Os dados históricos da associação são imutáveis: "
                    + ", ".join(changed)
                )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                # Não permite alterar a associação ou os snapshots.
                type(self).objects.select_for_update().get(pk=self.pk)
            else:
                # Obtém a cotação atual e verifica seu status.
                quotation = (
                    SupplierQuotation.objects
                    .select_for_update()
                    .select_related(
                        "supplier_location__supplier",
                        "material",
                    )
                    .get(pk=self.quotation_id)
                )

                if quotation.status != SupplierQuotation.Status.VALID:
                    raise ValidationError({
                        "quotation": (
                            "Somente cotações válidas podem ser "
                            "associadas a um orçamento."
                        )
                    })

                supplier = quotation.supplier_location.supplier
                location = quotation.supplier_location
                material = quotation.material

                self.supplier_name_snapshot = (
                    supplier.trade_name or supplier.legal_name
                )
                self.supplier_cnpj_snapshot = supplier.cnpj or ""

                self.location_name_snapshot = location.name
                self.street_snapshot = location.street
                self.number_snapshot = location.number
                self.complement_snapshot = location.complement
                self.municipality_snapshot = location.municipality
                self.state_snapshot = location.state
                self.postal_code_snapshot = location.postal_code

                self.material_code_snapshot = material.code
                self.material_description_snapshot = material.description

                self.quoted_at_snapshot = quotation.quoted_at
                self.valid_until_snapshot = quotation.valid_until
                self.unit_price_snapshot = quotation.unit_price
                self.unit_snapshot = quotation.unit
                self.source_document_snapshot = quotation.source_document

            self.full_clean()
            super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Budget {self.budget_id} - "
            f"Quotation {self.quotation_id}"
        )