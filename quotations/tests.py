from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from app.models import Budget, Project
from occurrences.models import (
    Material,
    Supplier,
    SupplierLocation,
    SupplierLocationMaterial,
)
from quotations.models import BudgetQuotation, SupplierQuotation


class QuotationTestBase(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Fornecedor de Teste Ltda.",
            trade_name="Fornecedor Teste",
            cnpj="11.222.333/0001-81",
        )

        self.location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade Goiânia",
            street="Avenida de Teste",
            number="100",
            municipality="Goiânia",
            state="GO",
            postal_code="74000000",
            latitude=Decimal("-16.686900"),
            longitude=Decimal("-49.264800"),
        )

        self.material = Material.objects.create(
            code="MAT-001",
            description="Brita 1",
            unit="m3",
        )

        SupplierLocationMaterial.objects.create(
            supplier_location=self.location,
            material=self.material,
        )

        self.project = Project.objects.create(
            name="Projeto de Teste",
        )

        self.budget = Budget.objects.create(
            project=self.project,
            source_file_uf="GO",
            methodology=Budget.Methodology.SC,
            type_system=Budget.TypeSystem.ON,
            monetary_base_date=date(2026, 10, 1),
        )

    def create_quotation(
        self,
        status=SupplierQuotation.Status.VALID,
        unit_price=Decimal("150.000000"),
    ):
        return SupplierQuotation.objects.create(
            supplier_location=self.location,
            material=self.material,
            quoted_at=date(2026, 10, 10),
            valid_until=date(2026, 11, 10),
            unit_price=unit_price,
            unit="m3",
            status=status,
            source_document="cotacao-teste.pdf",
        )


class SupplierQuotationValidationTests(QuotationTestBase):
    def test_accepts_positive_unit_price(self):
        quotation = self.create_quotation()

        self.assertEqual(
            quotation.unit_price,
            Decimal("150.000000"),
        )

    def test_rejects_zero_unit_price(self):
        with self.assertRaises(ValidationError):
            self.create_quotation(
                unit_price=Decimal("0.000000"),
            )

    def test_rejects_negative_unit_price(self):
        with self.assertRaises(ValidationError):
            self.create_quotation(
                unit_price=Decimal("-10.000000"),
            )

    def test_rejects_validity_before_quotation_date(self):
        quotation = SupplierQuotation(
            supplier_location=self.location,
            material=self.material,
            quoted_at=date(2026, 10, 10),
            valid_until=date(2026, 10, 9),
            unit_price=Decimal("150.000000"),
            unit="m3",
            status=SupplierQuotation.Status.VALID,
        )

        with self.assertRaises(ValidationError):
            quotation.save()


class BudgetQuotationTests(QuotationTestBase):
    def test_associates_valid_quotation(self):
        quotation = self.create_quotation()

        association = BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        self.assertEqual(association.budget_id, self.budget.id)
        self.assertEqual(association.quotation_id, quotation.id)

    def test_rejects_draft_quotation(self):
        quotation = self.create_quotation(
            status=SupplierQuotation.Status.DRAFT,
        )

        with self.assertRaises(ValidationError):
            BudgetQuotation.objects.create(
                budget=self.budget,
                quotation=quotation,
            )

    def test_rejects_expired_quotation(self):
        quotation = self.create_quotation(
            status=SupplierQuotation.Status.EXPIRED,
        )

        with self.assertRaises(ValidationError):
            BudgetQuotation.objects.create(
                budget=self.budget,
                quotation=quotation,
            )

    def test_rejects_cancelled_quotation(self):
        quotation = self.create_quotation(
            status=SupplierQuotation.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            BudgetQuotation.objects.create(
                budget=self.budget,
                quotation=quotation,
            )

    def test_populates_historical_snapshots(self):
        quotation = self.create_quotation()

        association = BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        self.assertEqual(
            association.supplier_name_snapshot,
            "Fornecedor Teste",
        )
        self.assertEqual(
            association.supplier_cnpj_snapshot,
            "11222333000181",
        )
        self.assertEqual(
            association.location_name_snapshot,
            "Unidade Goiânia",
        )
        self.assertEqual(
            association.material_code_snapshot,
            "MAT-001",
        )
        self.assertEqual(
            association.material_description_snapshot,
            "Brita 1",
        )
        self.assertEqual(
            association.unit_price_snapshot,
            Decimal("150.000000"),
        )
        self.assertEqual(
            association.source_document_snapshot,
            "cotacao-teste.pdf",
        )

    def test_snapshot_does_not_change_when_supplier_changes(self):
        quotation = self.create_quotation()

        association = BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        self.supplier.trade_name = "Novo Nome Comercial"
        self.supplier.save()

        association.refresh_from_db()

        self.assertEqual(
            association.supplier_name_snapshot,
            "Fornecedor Teste",
        )

    def test_snapshot_cannot_be_changed(self):
        quotation = self.create_quotation()

        association = BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        association.unit_price_snapshot = Decimal("999.000000")

        with self.assertRaises(ValidationError):
            association.save()

    def test_association_cannot_be_transferred_to_another_budget(self):
        quotation = self.create_quotation()

        association = BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        another_project = Project.objects.create(
            name="Outro Projeto",
        )

        another_budget = Budget.objects.create(
            project=another_project,
            source_file_uf="GO",
            methodology=Budget.Methodology.SC,
            type_system=Budget.TypeSystem.ON,
            monetary_base_date=date(2026, 10, 1),
        )

        association.budget = another_budget

        with self.assertRaises(ValidationError):
            association.save()

    def test_associated_quotation_cannot_be_cancelled(self):
        quotation = self.create_quotation()

        BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        quotation.status = SupplierQuotation.Status.CANCELLED

        with self.assertRaises(ValidationError):
            quotation.save()

    def test_associated_quotation_cannot_be_expired(self):
        quotation = self.create_quotation()

        BudgetQuotation.objects.create(
            budget=self.budget,
            quotation=quotation,
        )

        quotation.status = SupplierQuotation.Status.EXPIRED

        with self.assertRaises(ValidationError):
            quotation.save()