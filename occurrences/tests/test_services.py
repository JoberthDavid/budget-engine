from unittest.mock import patch

from django.test import TestCase

from occurrences.api.serializers import SupplierLocationSerializer
from occurrences.api.services import save_supplier_location
from occurrences.models import (
    Material,
    MaterialNature,
    Supplier,
    SupplierLocation,
    SupplierLocationMaterial,
    SupplierLocationMaterialNature,
)


class SupplierLocationServiceTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Fornecedor de Teste Ltda",
        )

        self.nature_a = MaterialNature.objects.create(
            code="brita",
            name="Brita",
            group_code="agregados",
            icon_key="stone",
        )

        self.nature_b = MaterialNature.objects.create(
            code="areia",
            name="Areia",
            group_code="agregados",
            icon_key="sand",
        )

        self.material_a = Material.objects.create(
            code="MAT-001",
            description="Brita graduada",
            unit="m3",
        )

        self.material_b = Material.objects.create(
            code="MAT-002",
            description="Areia média",
            unit="m3",
        )

        self.valid_data = {
            "supplier": self.supplier.pk,
            "name": "Unidade de Teste",
            "municipality": "Goiânia",
            "state": "GO",
            "postal_code": "74000000",
        }

    def create_location(self, data=None):
        serializer = SupplierLocationSerializer(
            data=data or self.valid_data,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        return save_supplier_location(serializer)

    def test_creates_location(self):
        location = self.create_location()

        self.assertTrue(
            SupplierLocation.objects.filter(pk=location.pk).exists()
        )

    def test_creates_nature_associations(self):
        location = self.create_location({
            **self.valid_data,
            "nature_ids": [
                self.nature_a.pk,
                self.nature_b.pk,
            ],
        })

        nature_ids = set(
            SupplierLocationMaterialNature.objects.filter(
                supplier_location=location,
            ).values_list("material_nature_id", flat=True)
        )

        self.assertEqual(
            nature_ids,
            {self.nature_a.pk, self.nature_b.pk},
        )

    def test_creates_material_associations(self):
        location = self.create_location({
            **self.valid_data,
            "material_ids": [
                self.material_a.pk,
                self.material_b.pk,
            ],
        })

        material_ids = set(
            SupplierLocationMaterial.objects.filter(
                supplier_location=location,
                active=True,
            ).values_list("material_id", flat=True)
        )

        self.assertEqual(
            material_ids,
            {self.material_a.pk, self.material_b.pk},
        )

    def test_patch_preserves_omitted_associations(self):
        location = self.create_location({
            **self.valid_data,
            "nature_ids": [self.nature_a.pk],
            "material_ids": [self.material_a.pk],
        })

        serializer = SupplierLocationSerializer(
            location,
            data={"name": "Unidade Atualizada"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        save_supplier_location(serializer)

        self.assertTrue(
            SupplierLocationMaterialNature.objects.filter(
                supplier_location=location,
                material_nature=self.nature_a,
            ).exists()
        )

        self.assertTrue(
            SupplierLocationMaterial.objects.filter(
                supplier_location=location,
                material=self.material_a,
                active=True,
            ).exists()
        )

    def test_replaces_nature_associations(self):
        location = self.create_location({
            **self.valid_data,
            "nature_ids": [self.nature_a.pk],
        })

        serializer = SupplierLocationSerializer(
            location,
            data={"nature_ids": [self.nature_b.pk]},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        save_supplier_location(serializer)

        nature_ids = set(
            SupplierLocationMaterialNature.objects.filter(
                supplier_location=location,
            ).values_list("material_nature_id", flat=True)
        )

        self.assertEqual(nature_ids, {self.nature_b.pk})

    def test_deactivates_removed_materials(self):
        location = self.create_location({
            **self.valid_data,
            "material_ids": [
                self.material_a.pk,
                self.material_b.pk,
            ],
        })

        serializer = SupplierLocationSerializer(
            location,
            data={"material_ids": [self.material_b.pk]},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        save_supplier_location(serializer)

        link_a = SupplierLocationMaterial.objects.get(
            supplier_location=location,
            material=self.material_a,
        )

        link_b = SupplierLocationMaterial.objects.get(
            supplier_location=location,
            material=self.material_b,
        )

        self.assertFalse(link_a.active)
        self.assertTrue(link_b.active)

    def test_reactivates_existing_material(self):
        location = self.create_location({
            **self.valid_data,
            "material_ids": [self.material_a.pk],
        })

        link = SupplierLocationMaterial.objects.get(
            supplier_location=location,
            material=self.material_a,
        )

        link.active = False
        link.save(update_fields=["active"])

        serializer = SupplierLocationSerializer(
            location,
            data={"material_ids": [self.material_a.pk]},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        save_supplier_location(serializer)

        link.refresh_from_db()

        self.assertTrue(link.active)

    def test_put_replaces_omitted_associations(self):
        location = self.create_location({
            **self.valid_data,
            "nature_ids": [self.nature_a.pk],
            "material_ids": [self.material_a.pk],
        })

        serializer = SupplierLocationSerializer(
            location,
            data={
                **self.valid_data,
                "name": "Unidade Substituída",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        save_supplier_location(serializer, replace=True)

        self.assertFalse(
            SupplierLocationMaterialNature.objects.filter(
                supplier_location=location,
            ).exists()
        )

        self.assertFalse(
            SupplierLocationMaterial.objects.get(
                supplier_location=location,
                material=self.material_a,
            ).active
        )

    def test_rolls_back_location_and_associations_on_failure(self):
        serializer = SupplierLocationSerializer(
            data={
                **self.valid_data,
                "nature_ids": [self.nature_a.pk],
                "material_ids": [self.material_a.pk],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with patch(
            "occurrences.api.services.sync_location_materials",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                save_supplier_location(serializer)

        self.assertFalse(
            SupplierLocation.objects.filter(
                name="Unidade de Teste",
            ).exists()
        )

        self.assertFalse(
            SupplierLocationMaterialNature.objects.exists()
        )
