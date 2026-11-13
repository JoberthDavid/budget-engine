from django.core.exceptions import ValidationError
from django.test import TestCase
from decimal import Decimal

from occurrences.models import Supplier, SupplierLocation


class SupplierValidationTests(TestCase):
    def test_accepts_and_normalizes_valid_cnpj(self):
        supplier = Supplier(
            legal_name="Fornecedor de Teste",
            cnpj="11.222.333/0001-81",
        )

        supplier.save()

        self.assertEqual(supplier.cnpj, "11222333000181")

    def test_rejects_invalid_cnpj_check_digits(self):
        supplier = Supplier(
            legal_name="Fornecedor Inválido",
            cnpj="11.222.333/0001-80",
        )

        with self.assertRaises(ValidationError):
            supplier.save()

    def test_rejects_repeated_digits_cnpj(self):
        supplier = Supplier(
            legal_name="Fornecedor Inválido",
            cnpj="11.111.111/1111-11",
        )

        with self.assertRaises(ValidationError):
            supplier.save()

    def test_accepts_supplier_without_cnpj(self):
        supplier = Supplier(
            legal_name="Fornecedor sem CNPJ",
        )

        supplier.save()

        self.assertIsNone(supplier.cnpj)


class SupplierLocationValidationTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Fornecedor de Teste",
        )

    def test_normalizes_lowercase_state(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade Goiânia",
            municipality="Goiânia",
            state="go",
        )

        location.save()

        self.assertEqual(location.state, "GO")

    def test_rejects_invalid_state(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade Inválida",
            municipality="Cidade Teste",
            state="XX",
        )

        with self.assertRaises(ValidationError):
            location.save()

    def test_normalizes_formatted_postal_code(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade Goiânia",
            municipality="Goiânia",
            state="GO",
            postal_code="74000-000",
        )

        location.save()

        self.assertEqual(location.postal_code, "74000000")

    def test_rejects_invalid_postal_code(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade Goiânia",
            municipality="Goiânia",
            state="GO",
            postal_code="7400A-000",
        )

        with self.assertRaises(ValidationError):
            location.save()

    def test_accepts_location_without_coordinates(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade sem coordenadas",
            municipality="Goiânia",
            state="GO",
        )

        self.assertIsNone(location.latitude)
        self.assertIsNone(location.longitude)

    def test_rejects_only_latitude(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade incompleta",
            municipality="Goiânia",
            state="GO",
            latitude=Decimal("-16.686900"),
        )

        with self.assertRaises(ValidationError):
            location.save()

    def test_rejects_only_longitude(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade incompleta",
            municipality="Goiânia",
            state="GO",
            longitude=Decimal("-49.264800"),
        )

        with self.assertRaises(ValidationError):
            location.save()

    def test_accepts_valid_coordinates(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade georreferenciada",
            municipality="Goiânia",
            state="GO",
            latitude=Decimal("-16.686900"),
            longitude=Decimal("-49.264800"),
        )

        self.assertEqual(str(location.latitude), "-16.686900")
        self.assertEqual(str(location.longitude), "-49.264800")

    def test_rejects_latitude_out_of_range(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade inválida",
            municipality="Goiânia",
            state="GO",
            latitude=91,
            longitude=-49.2648,
        )

        with self.assertRaises(ValidationError):
            location.save()

    def test_rejects_longitude_out_of_range(self):
        location = SupplierLocation(
            supplier=self.supplier,
            name="Unidade inválida",
            municipality="Goiânia",
            state="GO",
            latitude=-16.6869,
            longitude=181,
        )

        with self.assertRaises(ValidationError):
            location.save()