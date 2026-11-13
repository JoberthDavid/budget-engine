from types import SimpleNamespace

from django.test import TestCase
from rest_framework.test import APIClient

from decimal import Decimal

from occurrences.api.serializers import SupplierLocationSerializer
from occurrences.models import (
    Material,
    MaterialNature,
    Supplier,
    SupplierLocation,
)


class SupplierAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = SimpleNamespace(
            is_authenticated=True,
            is_anonymous=False,
            username="user:test",
        )

        self.supplier = Supplier.objects.create(
            legal_name="Empresa de Agregados Ltda",
            trade_name="Pedreira Central",
            cnpj="11222333000181",
            phone="(62) 3333-3333",
            email="contato@empresa.com.br",
        )

    def authenticate_with_scope(self, *scopes):
        self.client.force_authenticate(
            user=self.user,
            token={
                "sub": "user:test",
                "scope": list(scopes),
            },
        )

    def test_list_suppliers_returns_active_suppliers(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:read"
        )

        response = self.client.get("/occurrences/suppliers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["legal_name"],
            "Empresa de Agregados Ltda",
        )

    def test_create_supplier(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:create"
        )

        payload = {
            "legal_name": "Construtora Exemplo Ltda",
            "trade_name": "Construtora Exemplo",
            "cnpj": "12345678000195",
            "email": "contato@exemplo.com.br",
        }

        response = self.client.post(
            "/occurrences/suppliers",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["legal_name"],
            "Construtora Exemplo Ltda",
        )
        self.assertTrue(
            Supplier.objects.filter(
                cnpj="12345678000195"
            ).exists()
        )

    def test_create_supplier_with_invalid_cnpj_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:create"
        )

        response = self.client.post(
            "/occurrences/suppliers",
            {
                "legal_name": "Empresa com CNPJ inválido",
                "cnpj": "11111111111111",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_create_supplier_with_duplicate_cnpj_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:create"
        )

        response = self.client.post(
            "/occurrences/suppliers",
            {
                "legal_name": "Empresa duplicada Ltda",
                "cnpj": "11222333000181",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_get_supplier_detail(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:read"
        )

        response = self.client.get(
            f"/occurrences/suppliers/{self.supplier.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["id"],
            self.supplier.pk,
        )

    def test_get_nonexistent_supplier_returns_404(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:read"
        )

        response = self.client.get(
            "/occurrences/suppliers/999999"
        )

        self.assertEqual(response.status_code, 404)

    def test_patch_supplier_updates_only_informed_fields(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:update"
        )

        response = self.client.patch(
            f"/occurrences/suppliers/{self.supplier.pk}",
            {"trade_name": "Pedreira Atualizada"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.supplier.refresh_from_db()

        self.assertEqual(
            self.supplier.trade_name,
            "Pedreira Atualizada",
        )
        self.assertEqual(
            self.supplier.legal_name,
            "Empresa de Agregados Ltda",
        )

    def test_put_supplier_updates_supplier(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:update"
        )

        response = self.client.put(
            f"/occurrences/suppliers/{self.supplier.pk}",
            {
                "legal_name": "Empresa Atualizada Ltda",
                "trade_name": "Empresa Atualizada",
                "cnpj": "11222333000181",
                "phone": "(62) 3000-0000",
                "email": "novo@empresa.com.br",
                "legal_representative": "Representante",
                "representative_email": "representante@empresa.com.br",
                "representative_phone": "(62) 99999-9999",
                "active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["legal_name"],
            "Empresa Atualizada Ltda",
        )

    def test_delete_supplier_deactivates_supplier(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:delete"
        )

        response = self.client.delete(
            f"/occurrences/suppliers/{self.supplier.pk}"
        )

        self.assertEqual(response.status_code, 204)

        self.supplier.refresh_from_db()
        self.assertFalse(self.supplier.active)

    def test_list_suppliers_does_not_return_inactive_suppliers(self):
        self.supplier.active = False
        self.supplier.save()

        self.authenticate_with_scope(
            "occurrences:suppliers:read"
        )

        response = self.client.get("/occurrences/suppliers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_suppliers_without_authentication_returns_401(self):
        response = self.client.get("/occurrences/suppliers")

        self.assertEqual(response.status_code, 401)

    def test_list_suppliers_without_scope_returns_403(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:create"
        )

        response = self.client.get("/occurrences/suppliers")

        self.assertEqual(response.status_code, 403)

    def test_create_supplier_without_create_scope_returns_403(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:read"
        )

        response = self.client.post(
            "/occurrences/suppliers",
            {"legal_name": "Empresa sem autorização"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_put_supplier_requires_legal_name(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:update"
        )

        response = self.client.put(
            f"/occurrences/suppliers/{self.supplier.pk}",
            {
                "trade_name": "Empresa Atualizada",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_get_inactive_supplier_detail(self):
        self.supplier.active = False
        self.supplier.save()

        self.authenticate_with_scope(
            "occurrences:suppliers:read"
        )

        response = self.client.get(
            f"/occurrences/suppliers/{self.supplier.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["active"])

    def test_delete_supplier_with_linked_location(self):
        from occurrences.models import SupplierLocation

        SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de teste",
            municipality="Goiânia",
            state="GO",
        )

        self.authenticate_with_scope(
            "occurrences:suppliers:delete"
        )

        response = self.client.delete(
            f"/occurrences/suppliers/{self.supplier.pk}"
        )

        self.assertEqual(response.status_code, 204)

        self.supplier.refresh_from_db()
        self.assertFalse(self.supplier.active)

        self.assertTrue(
            self.supplier.locations.filter(active=True).exists()
        )

    def test_put_supplier_resets_omitted_optional_fields(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:update"
        )

        response = self.client.put(
            f"/occurrences/suppliers/{self.supplier.pk}",
            {
                "legal_name": "Empresa Substituída Ltda",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.supplier.refresh_from_db()

        self.assertEqual(
            self.supplier.legal_name,
            "Empresa Substituída Ltda",
        )
        self.assertEqual(self.supplier.trade_name, "")
        self.assertIsNone(self.supplier.cnpj)
        self.assertEqual(self.supplier.phone, "")
        self.assertEqual(self.supplier.email, "")
        self.assertTrue(self.supplier.active)

    def test_patch_supplier_preserves_omitted_optional_fields(self):
        self.authenticate_with_scope(
            "occurrences:suppliers:update"
        )

        original_cnpj = self.supplier.cnpj
        original_email = self.supplier.email

        response = self.client.patch(
            f"/occurrences/suppliers/{self.supplier.pk}",
            {
                "legal_name": "Empresa Parcialmente Atualizada Ltda",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.supplier.refresh_from_db()

        self.assertEqual(self.supplier.cnpj, original_cnpj)
        self.assertEqual(self.supplier.email, original_email)
        self.assertEqual(
            self.supplier.legal_name,
            "Empresa Parcialmente Atualizada Ltda",
        )


class SupplierLocationSerializerTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Fornecedor de Teste Ltda",
        )
        self.nature = MaterialNature.objects.create(
            code="brita",
            name="Brita",
            group_code="agregados",
            icon_key="stone",
        )
        self.material = Material.objects.create(
            code="MAT-001",
            description="Brita graduada",
            unit="m3",
        )
        self.valid_data = {
            "supplier": self.supplier.pk,
            "name": "Unidade de Teste",
            "municipality": "Goiânia",
            "state": "go",
            "postal_code": "74000-000",
        }

    def test_accepts_valid_location(self):
        serializer = SupplierLocationSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_normalizes_state(self):
        serializer = SupplierLocationSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["state"], "GO")

    def test_normalizes_postal_code(self):
        data = {
            **self.valid_data,
            "postal_code": "74000-000",
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["postal_code"],
            "74000000",
        )

    def test_rejects_invalid_state(self):
        data = {
            **self.valid_data,
            "state": "XX",
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("state", serializer.errors)

    def test_rejects_invalid_postal_code(self):
        data = {
            **self.valid_data,
            "postal_code": "123",
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("postal_code", serializer.errors)

    def test_rejects_coordinates_without_pair(self):
        data = {
            **self.valid_data,
            "latitude": "-16.6869",
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("latitude", serializer.errors)

    def test_accepts_valid_coordinates(self):
        data = {
            **self.valid_data,
            "latitude": "-16.6869",
            "longitude": "-49.2648",
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_invalid_nature_id(self):
        data = {
            **self.valid_data,
            "nature_ids": [9999],
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("nature_ids", serializer.errors)

    def test_accepts_existing_nature(self):
        data = {
            **self.valid_data,
            "nature_ids": [self.nature.pk],
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_duplicate_nature_ids(self):
        data = {
            **self.valid_data,
            "nature_ids": [self.nature.pk, self.nature.pk],
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("nature_ids", serializer.errors)

    def test_rejects_invalid_material_id(self):
        data = {
            **self.valid_data,
            "material_ids": [9999],
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("material_ids", serializer.errors)

    def test_accepts_existing_material(self):
        data = {
            **self.valid_data,
            "material_ids": [self.material.pk],
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_patch_updates_only_latitude(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000-000",
            latitude="-16.6869",
            longitude="-49.2648",
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"latitude": "-16.7000"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertEqual(
            serializer.validated_data["latitude"],
            Decimal("-16.7000"),
        )
        self.assertNotIn("longitude", serializer.validated_data)

    def test_patch_updates_only_longitude(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000-000",
            latitude="-16.6869",
            longitude="-49.2648",
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"longitude": "-49.3000"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertNotIn("latitude", serializer.validated_data)
        self.assertEqual(
            serializer.validated_data["longitude"],
            Decimal("-49.3000"),
        )

    def test_patch_preserves_coordinates_when_omitted(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000-000",
            latitude="-16.6869",
            longitude="-49.2648",
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"name": "Unidade Atualizada"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("latitude", serializer.validated_data)
        self.assertNotIn("longitude", serializer.validated_data)

    def test_patch_rejects_null_latitude_without_null_longitude(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000-000",
            latitude="-16.6869",
            longitude="-49.2648",
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"latitude": None},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("latitude", serializer.errors)

    def test_patch_accepts_null_coordinates_together(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000-000",
            latitude="-16.6869",
            longitude="-49.2648",
        )

        serializer = SupplierLocationSerializer(
            location,
            data={
                "latitude": None,
                "longitude": None,
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsNone(serializer.validated_data["latitude"])
        self.assertIsNone(serializer.validated_data["longitude"])

    def test_rejects_inactive_supplier_on_create(self):
        inactive_supplier = Supplier.objects.create(
            legal_name="Fornecedor Inativo Ltda",
            active=False,
        )

        data = {
            **self.valid_data,
            "supplier": inactive_supplier.pk,
        }
        serializer = SupplierLocationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("supplier", serializer.errors)


    def test_accepts_current_inactive_supplier_on_update(self):
        self.supplier.active = False
        self.supplier.save()

        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000000",
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"supplier": self.supplier.pk},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)


    def test_rejects_switching_to_inactive_supplier(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000000",
        )

        inactive_supplier = Supplier.objects.create(
            legal_name="Fornecedor Inativo Ltda",
            active=False,
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"supplier": inactive_supplier.pk},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("supplier", serializer.errors)


    def test_accepts_switching_to_active_supplier(self):
        location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade de Teste",
            municipality="Goiânia",
            state="GO",
            postal_code="74000000",
        )

        new_supplier = Supplier.objects.create(
            legal_name="Novo Fornecedor Ltda",
            active=True,
        )

        serializer = SupplierLocationSerializer(
            location,
            data={"supplier": new_supplier.pk},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

class SupplierLocationAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = SimpleNamespace(
            is_authenticated=True,
            is_anonymous=False,
            username="user:test",
        )

        self.supplier = Supplier.objects.create(
            legal_name="Fornecedor de Teste Ltda",
        )

        self.location = SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade Central",
            municipality="Goiânia",
            state="GO",
            postal_code="74000000",
        )

    def authenticate_with_scope(self, *scopes):
        self.client.force_authenticate(
            user=self.user,
            token={
                "sub": "user:test",
                "scope": list(scopes),
            },
        )

    def valid_payload(self):
        return {
            "supplier": self.supplier.pk,
            "name": "Nova Unidade",
            "municipality": "Goiânia",
            "state": "GO",
            "postal_code": "74000000",
        }

    def test_create_location(self):
        self.authenticate_with_scope(
            "occurrences:locations:create"
        )

        response = self.client.post(
            "/occurrences/locations",
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            SupplierLocation.objects.filter(
                name="Nova Unidade"
            ).count(),
            1,
        )

    def test_create_location_without_create_scope_returns_403(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.post(
            "/occurrences/locations",
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_list_locations(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get("/occurrences/locations")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_list_locations_excludes_inactive_locations(self):
        SupplierLocation.objects.create(
            supplier=self.supplier,
            name="Unidade Inativa",
            municipality="Anápolis",
            state="GO",
            active=False,
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get("/occurrences/locations")

        self.assertEqual(response.status_code, 200)

        names = [item["name"] for item in response.json()]

        self.assertIn("Unidade Central", names)
        self.assertNotIn("Unidade Inativa", names)

    def test_get_location_detail(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            f"/occurrences/locations/{self.location.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["name"],
            "Unidade Central",
        )

    def test_patch_location_preserves_omitted_fields(self):
        self.authenticate_with_scope(
            "occurrences:locations:update"
        )

        response = self.client.patch(
            f"/occurrences/locations/{self.location.pk}",
            {"name": "Unidade Atualizada"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.location.refresh_from_db()

        self.assertEqual(
            self.location.name,
            "Unidade Atualizada",
        )
        self.assertEqual(
            self.location.municipality,
            "Goiânia",
        )
        self.assertEqual(self.location.state, "GO")

    def test_put_location_replaces_omitted_optional_fields(self):
        self.location.street = "Rua de Teste"
        self.location.number = "100"
        self.location.save()

        self.authenticate_with_scope(
            "occurrences:locations:update"
        )

        response = self.client.put(
            f"/occurrences/locations/{self.location.pk}",
            {
                "supplier": self.supplier.pk,
                "name": "Unidade Substituída",
                "municipality": "Anápolis",
                "state": "GO",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.location.refresh_from_db()

        self.assertEqual(
            self.location.name,
            "Unidade Substituída",
        )
        self.assertEqual(self.location.municipality, "Anápolis")
        self.assertEqual(self.location.street, "")
        self.assertEqual(self.location.number, "")
        self.assertEqual(self.location.source, "MANUAL")

    def test_delete_location_is_logical(self):
        self.authenticate_with_scope(
            "occurrences:locations:delete"
        )

        response = self.client.delete(
            f"/occurrences/locations/{self.location.pk}"
        )

        self.assertEqual(response.status_code, 204)

        self.location.refresh_from_db()

        self.assertFalse(self.location.active)

    def test_get_inactive_location_detail(self):
        self.location.active = False
        self.location.save()

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            f"/occurrences/locations/{self.location.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["active"])

    def test_get_nonexistent_location_returns_404(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations/999999"
        )

        self.assertEqual(response.status_code, 404)

    def test_filter_locations_by_supplier(self):
        other_supplier = Supplier.objects.create(
            legal_name="Outro Fornecedor Ltda",
        )

        SupplierLocation.objects.create(
            supplier=other_supplier,
            name="Unidade de Anápolis",
            municipality="Anápolis",
            state="GO",
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"supplier_id": self.supplier.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["name"],
            "Unidade Central",
        )

    def test_filter_locations_by_state(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"state": "go"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_locations_by_municipality(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"municipality": "goi"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_locations_by_material(self):
        material = Material.objects.create(
            code="MAT-001",
            description="Brita graduada",
            unit="m3",
        )

        self.location.material_links.create(
            material=material,
            active=True,
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"material_id": material.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_locations_by_nature(self):
        nature = MaterialNature.objects.create(
            code="brita",
            name="Brita",
            group_code="agregados",
            icon_key="stone",
        )

        self.location.nature_links.create(
            material_nature=nature,
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"nature_id": nature.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_locations_by_active_material_status(self):
        material = Material.objects.create(
            code="MAT-002",
            description="Areia",
            unit="m3",
        )

        self.location.material_links.create(
            material=material,
            active=True,
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"material_status": "active"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_locations_by_inactive_material_status(self):
        material = Material.objects.create(
            code="MAT-003",
            description="Cimento",
            unit="kg",
        )

        self.location.material_links.create(
            material=material,
            active=False,
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"material_status": "inactive"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_locations_by_combined_parameters(self):
        material = Material.objects.create(
            code="MAT-004",
            description="Solo brita",
            unit="m3",
        )

        self.location.material_links.create(
            material=material,
            active=True,
        )

        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {
                "supplier_id": self.supplier.pk,
                "state": "GO",
                "municipality": "Goiânia",
                "material_id": material.pk,
                "material_status": "active",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_invalid_supplier_id_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"supplier_id": "abc"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("supplier_id", response.json()["details"])
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_zero_material_id_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"material_id": "0"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("material_id", response.json()["details"])
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_invalid_nature_id_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"nature_id": "-1"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("nature_id", response.json()["details"])
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_invalid_state_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"state": "XX"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("state", response.json()["details"])
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_empty_municipality_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"municipality": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("municipality", response.json()["details"])
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_invalid_material_status_returns_400(self):
        self.authenticate_with_scope(
            "occurrences:locations:read"
        )

        response = self.client.get(
            "/occurrences/locations",
            {"material_status": "unknown"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("material_status", response.json()["details"])
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )
