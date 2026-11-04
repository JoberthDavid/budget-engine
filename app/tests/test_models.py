from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from app.models import (
    BDI,
    BDIMethod,
    Budget,
    BudgetBDI,
    BudgetComposition,
    BudgetService,
    Project,
)


class BudgetModelTestCase(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Projeto de teste",
        )

        self.budget = Budget.objects.create(
            project=self.project,
            source_file_uf="GO",
            methodology=Budget.Methodology.SC,
            type_system=Budget.TypeSystem.ON,
            monetary_base_date=date(2026, 1, 1),
        )

        self.bdi_method = BDIMethod.objects.create(
            method="BDI Teste",
        )

        self.bdi = BDI.objects.create(
            name="BDI Teste",
            slug="bdi-teste",
            method=self.bdi_method,
        )

        self.budget_bdi = BudgetBDI.objects.create(
            budget=self.budget,
            bdi=self.bdi,
        )

    def create_service(self, **kwargs):
        defaults = {
            "budget": self.budget,
            "code": "SERV-001",
            "description": "Serviço de teste",
            "unit": "m³",
            "quantity": Decimal("100.000000"),
        }

        defaults.update(kwargs)

        return BudgetService.objects.create(**defaults)

    def create_composition(self, service, **kwargs):
        defaults = {
            "budget": self.budget,
            "service": service,
            "budget_bdi": self.budget_bdi,
            "composition_id": "4915757",
            "reference_base_date": date(2026, 1, 1),
            "factor": Decimal("1.000000"),
        }

        defaults.update(kwargs)

        return BudgetComposition.objects.create(**defaults)

    def test_budget_service_receives_first_label_automatically(self):
        service = self.create_service()

        self.assertEqual(service.label, 1)

    def test_budget_service_receives_sequential_labels(self):
        service_1 = self.create_service(
            code="SERV-001",
        )

        service_2 = self.create_service(
            code="SERV-002",
        )

        service_3 = self.create_service(
            code="SERV-003",
        )

        self.assertEqual(service_1.label, 1)
        self.assertEqual(service_2.label, 2)
        self.assertEqual(service_3.label, 3)

    def test_budget_service_has_independent_sequence_per_budget(self):
        project_2 = Project.objects.create(
            name="Projeto 2",
        )

        budget_2 = Budget.objects.create(
            project=project_2,
            source_file_uf="GO",
            methodology=Budget.Methodology.SC,
            type_system=Budget.TypeSystem.ON,
            monetary_base_date=date(2026, 1, 1),
        )

        service_1 = self.create_service()

        service_2 = BudgetService.objects.create(
            budget=budget_2,
            code="SERV-001",
            description="Serviço de outro orçamento",
            unit="m³",
            quantity=Decimal("50.000000"),
        )

        self.assertEqual(service_1.label, 1)
        self.assertEqual(service_2.label, 1)

    def test_budget_service_allows_user_defined_label(self):
        service = self.create_service(
            label=10,
        )

        self.assertEqual(service.label, 10)

    def test_budget_service_allows_label_change(self):
        service = self.create_service()

        self.assertEqual(service.label, 1)

        service.label = 10
        service.save()

        service.refresh_from_db()

        self.assertEqual(service.label, 10)

    def test_budget_composition_receives_first_label_automatically(self):
        service = self.create_service()

        composition = self.create_composition(service)

        self.assertEqual(composition.label, 1)

    def test_budget_composition_receives_sequential_labels_per_service(self):
        service = self.create_service()

        composition_1 = self.create_composition(
            service,
            composition_id="COMP-001",
        )

        composition_2 = self.create_composition(
            service,
            composition_id="COMP-002",
        )

        composition_3 = self.create_composition(
            service,
            composition_id="COMP-003",
        )

        self.assertEqual(composition_1.label, 1)
        self.assertEqual(composition_2.label, 2)
        self.assertEqual(composition_3.label, 3)

    def test_budget_composition_has_independent_sequence_per_service(self):
        service_1 = self.create_service(
            code="SERV-001",
        )

        service_2 = self.create_service(
            code="SERV-002",
        )

        composition_1 = self.create_composition(
            service_1,
            composition_id="COMP-001",
        )

        composition_2 = self.create_composition(
            service_2,
            composition_id="COMP-002",
        )

        self.assertEqual(composition_1.label, 1)
        self.assertEqual(composition_2.label, 1)

    def test_budget_composition_allows_user_defined_label(self):
        service = self.create_service()

        composition = self.create_composition(
            service,
            label=10,
        )

        self.assertEqual(composition.label, 10)

    def test_budget_composition_allows_label_change(self):
        service = self.create_service()

        composition = self.create_composition(service)

        self.assertEqual(composition.label, 1)

        composition.label = 10
        composition.save()

        composition.refresh_from_db()

        self.assertEqual(composition.label, 10)

    def test_budget_composition_clean_accepts_same_budget(self):
        service = self.create_service()

        composition = BudgetComposition(
            budget=self.budget,
            service=service,
            budget_bdi=self.budget_bdi,
            composition_id="4915757",
            reference_base_date=date(2026, 1, 1),
            factor=Decimal("1.000000"),
        )

        composition.full_clean()

    def test_budget_composition_clean_rejects_service_from_another_budget(self):
        project_2 = Project.objects.create(
            name="Projeto 2",
        )

        budget_2 = Budget.objects.create(
            project=project_2,
            source_file_uf="GO",
            methodology=Budget.Methodology.SC,
            type_system=Budget.TypeSystem.ON,
            monetary_base_date=date(2026, 1, 1),
        )

        service_2 = BudgetService.objects.create(
            budget=budget_2,
            code="SERV-002",
            description="Serviço de outro orçamento",
            unit="m³",
            quantity=Decimal("50.000000"),
        )

        composition = BudgetComposition(
            budget=self.budget,
            service=service_2,
            budget_bdi=self.budget_bdi,
            composition_id="4915757",
            reference_base_date=date(2026, 1, 1),
            factor=Decimal("1.000000"),
        )

        with self.assertRaises(ValidationError) as context:
            composition.full_clean()

        self.assertIn("service", context.exception.message_dict)

    def test_budget_composition_clean_rejects_bdi_from_another_budget(self):
        project_2 = Project.objects.create(
            name="Projeto 2",
        )

        budget_2 = Budget.objects.create(
            project=project_2,
            source_file_uf="GO",
            methodology=Budget.Methodology.SC,
            type_system=Budget.TypeSystem.ON,
            monetary_base_date=date(2026, 1, 1),
        )

        bdi_2 = BDI.objects.create(
            name="BDI 2",
            slug="bdi-2",
            method=self.bdi_method,
        )

        budget_bdi_2 = BudgetBDI.objects.create(
            budget=budget_2,
            bdi=bdi_2,
        )

        service = self.create_service()

        composition = BudgetComposition(
            budget=self.budget,
            service=service,
            budget_bdi=budget_bdi_2,
            composition_id="4915757",
            reference_base_date=date(2026, 1, 1),
            factor=Decimal("1.000000"),
        )

        with self.assertRaises(ValidationError) as context:
            composition.full_clean()

        self.assertIn("budget_bdi", context.exception.message_dict)

    def test_budget_service_does_not_allow_duplicate_label_in_same_budget(self):
        self.create_service(
            label=1,
            code="SERV-001",
        )

        service = BudgetService(
            budget=self.budget,
            label=1,
            code="SERV-002",
            description="Serviço duplicado",
            unit="m³",
            quantity=Decimal("50.000000"),
        )

        with self.assertRaises(ValidationError):
            service.validate_constraints()

    def test_budget_composition_does_not_allow_duplicate_label_in_same_service(self):
        service = self.create_service()

        self.create_composition(
            service,
            label=1,
            composition_id="COMP-001",
        )

        composition = BudgetComposition(
            budget=self.budget,
            service=service,
            budget_bdi=self.budget_bdi,
            label=1,
            composition_id="COMP-002",
            reference_base_date=date(2026, 1, 1),
            factor=Decimal("1.000000"),
        )

        with self.assertRaises(ValidationError):
            composition.validate_constraints()

    def test_budget_service_database_rejects_duplicate_label(self):
        self.create_service(
            label=1,
            code="SERV-001",
        )

        service = BudgetService(
            budget=self.budget,
            label=1,
            code="SERV-002",
            description="Serviço duplicado",
            unit="m³",
            quantity=Decimal("50.000000"),
        )

        with self.assertRaises(IntegrityError):
            service.save(force_insert=True)

    def test_budget_composition_database_rejects_duplicate_label(self):
        service = self.create_service()

        self.create_composition(
            service,
            label=1,
            composition_id="COMP-001",
        )

        composition = BudgetComposition(
            budget=self.budget,
            service=service,
            budget_bdi=self.budget_bdi,
            label=1,
            composition_id="COMP-002",
            reference_base_date=date(2026, 1, 1),
            factor=Decimal("1.000000"),
        )

        with self.assertRaises(IntegrityError):
            composition.save(force_insert=True)