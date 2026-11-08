from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .validators import (
    BRAZILIAN_STATES,
    normalize_cnpj,
    normalize_postal_code,
    normalize_state,
)


class Supplier(models.Model):
    legal_name = models.CharField(max_length=200)
    trade_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )
    cnpj = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
    )

    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    legal_representative = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )
    representative_email = models.EmailField(
        blank=True,
        default="",
    )
    representative_phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        ordering = ["legal_name"]

    def clean(self):
        super().clean()

        if self.cnpj:
            self.cnpj = normalize_cnpj(self.cnpj)

    def save(self, *args, **kwargs):
        # Normaliza antes do full_clean(), pois max_length é
        # validado antes da execução de clean().
        if self.cnpj:
            self.cnpj = normalize_cnpj(self.cnpj)

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.trade_name or self.legal_name


class MaterialNature(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    group_code = models.CharField(max_length=50)
    icon_key = models.CharField(max_length=50)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "material_natures"
        ordering = ["group_code", "name"]

    def __str__(self):
        return self.name


class SupplierLocation(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="locations",
    )

    name = models.CharField(max_length=200)

    street = models.CharField(max_length=200, blank=True, default="")
    number = models.CharField(max_length=30, blank=True, default="")
    complement = models.CharField(max_length=100, blank=True, default="")
    neighborhood = models.CharField(max_length=100, blank=True, default="")
    municipality = models.CharField(max_length=150)
    state = models.CharField(max_length=2, choices=BRAZILIAN_STATES)
    postal_code = models.CharField(max_length=9, blank=True, default="")

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )

    natures = models.ManyToManyField(
        MaterialNature,
        through="SupplierLocationMaterialNature",
        related_name="supplier_locations",
    )

    source = models.CharField(
        max_length=20,
        choices=[
            ("MANUAL", "Manual"),
            ("DNIT", "DNIT"),
            ("SIGMINE", "SIGMINE"),
            ("API", "API"),
        ],
        default="MANUAL",
    )
    external_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "supplier_locations"
        ordering = ["municipality", "name"]
        indexes = [
            models.Index(
                fields=["state", "municipality"],
                name="supplier_loc_state_city_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(latitude__isnull=True, longitude__isnull=True)
                    | Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name="location_coordinates_together",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if self.state:
            try:
                self.state = normalize_state(self.state)
            except ValidationError as exc:
                errors["state"] = exc.messages

        if self.postal_code:
            try:
                self.postal_code = normalize_postal_code(
                    self.postal_code
                )
            except ValidationError as exc:
                errors["postal_code"] = exc.messages

        if (self.latitude is None) != (self.longitude is None):
            errors["latitude"] = (
                "Latitude e longitude devem ser informadas juntas."
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.state:
            self.state = self.state.strip().upper()

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.municipality}/{self.state}"


class SupplierLocationMaterialNature(models.Model):
    supplier_location = models.ForeignKey(
        SupplierLocation,
        on_delete=models.PROTECT,
        related_name="nature_links",
    )
    material_nature = models.ForeignKey(
        MaterialNature,
        on_delete=models.PROTECT,
        related_name="location_links",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "supplier_location_material_natures"
        constraints = [
            models.UniqueConstraint(
                fields=["supplier_location", "material_nature"],
                name="unique_location_material_nature",
            ),
        ]

    def __str__(self):
        return f"{self.supplier_location} - {self.material_nature}"


class Material(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=250)
    unit = models.CharField(max_length=30)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "materials"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.description}"


class SupplierLocationMaterial(models.Model):
    supplier_location = models.ForeignKey(
        SupplierLocation,
        on_delete=models.PROTECT,
        related_name="material_links",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="supplier_links",
    )

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "supplier_location_materials"
        constraints = [
            models.UniqueConstraint(
                fields=["supplier_location", "material"],
                name="unique_location_material",
            ),
        ]

    def __str__(self):
        return f"{self.supplier_location} - {self.material}"