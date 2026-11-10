from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from bdi.models import BDI, BDIQuota, BDIMethod
from bdi.api.serializers import (
    BDICreateSerializer,
    BDIUpdateSerializer,
)


class BDIAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.method = BDIMethod.objects.create(
            method="SICRO",
        )

        self.bdi = BDI.objects.create(
            name="BDI Onerado",
            slug="bdi-onerado",
            method=self.method,
            observation="BDI de teste.",
        )

        BDIQuota.objects.create(
            bdi=self.bdi,
            group="A",
            description="ADMINISTRAÇÃO CENTRAL",
            percentage=Decimal("3.000000"),
            variable="AC",
            base="CD",
        )

        BDIQuota.objects.create(
            bdi=self.bdi,
            group="D",
            description="LUCRO",
            percentage=Decimal("8.000000"),
            variable="L",
            base="CD",
        )

    def test_get_bdi_returns_bdi_with_quotas(self):
        response = self.client.get(
            f"/bdi/{self.bdi.id}"
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["id"], self.bdi.id)
        self.assertEqual(data["name"], "BDI Onerado")
        self.assertEqual(data["slug"], "bdi-onerado")

        self.assertEqual(
            data["method"]["id"],
            self.method.id,
        )

        self.assertEqual(
            data["method"]["method"],
            "SICRO",
        )

        self.assertEqual(len(data["quotas"]), 2)

        self.assertEqual(
            data["quotas"][0]["description"],
            "ADMINISTRAÇÃO CENTRAL",
        )

        self.assertEqual(
            data["quotas"][0]["percentage"],
            "3.000000",
        )
        self.assertEqual(
            data["observation"],
            "BDI de teste.",
        )
        self.assertEqual(
            data["quotas"][0]["base"],
            "CD",
        )

    def test_get_nonexistent_bdi_returns_404(self):
        response = self.client.get("/bdi/999999")

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.json(),
            {"detail": "BDI não encontrado."},
        )

    def test_list_bdis_returns_bdi(self):
        response = self.client.get("/bdi")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.bdi.id)
        self.assertEqual(data[0]["name"], "BDI Onerado")

    def test_create_serializer_accepts_bdi_aggregate(self):
        serializer = BDICreateSerializer(
            data={
                "name": "BDI Teste",
                "slug": "bdi-teste",
                "method_id": self.method.id,
                "observation": "Observação.",
                "quotas": [
                    {
                        "group": "A",
                        "description": "ADMINISTRAÇÃO CENTRAL",
                        "percentage": "9.000000",
                        "variable": "AC",
                        "base": "CD",
                    },
                    {
                        "group": "D",
                        "description": "LUCRO",
                        "percentage": "12.000000",
                        "variable": "L",
                        "base": "CD",
                    },
                ],
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_update_serializer_requires_complete_bdi(self):

        serializer = BDIUpdateSerializer(
            data={
                "name": "BDI Atualizado",
            }
        )

        self.assertFalse(
            serializer.is_valid()
        )

        self.assertIn("slug", serializer.errors)
        self.assertIn("method_id", serializer.errors)
        self.assertIn("quotas", serializer.errors)

    def test_update_serializer_accepts_quotas(self):
        serializer = BDIUpdateSerializer(
            data={
                "name": "BDI Atualizado",
                "slug": "bdi-atualizado",
                "method_id": self.method.id,
                "observation": "Observação atualizada.",
                "quotas": [
                    {
                        "group": "A",
                        "description": "ADMINISTRAÇÃO CENTRAL",
                        "percentage": "9.000000",
                        "variable": "AC",
                        "base": "CD",
                    },
                    {
                        "group": "D",
                        "description": "LUCRO",
                        "percentage": "12.000000",
                        "variable": "L",
                        "base": "CD",
                    },
                ],
            }
        )

        self.assertTrue(
            serializer.is_valid(),
            serializer.errors,
        )

    def test_create_bdi_creates_bdi_and_quotas(self):
        response = self.client.post(
            "/bdi",
            data={
                "name": "BDI Novo",
                "slug": "bdi-novo",
                "method_id": self.method.id,
                "observation": "BDI criado pela API.",
                "quotas": [
                    {
                        "group": "A",
                        "description": "ADMINISTRAÇÃO CENTRAL",
                        "percentage": "9.000000",
                        "variable": "AC",
                        "base": "CD",
                    },
                    {
                        "group": "D",
                        "description": "LUCRO",
                        "percentage": "12.000000",
                        "variable": "L",
                        "base": "CD",
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        bdi = BDI.objects.get(slug="bdi-novo")

        self.assertEqual(bdi.name, "BDI Novo")
        self.assertEqual(bdi.method_id, self.method.id)
        self.assertEqual(
            bdi.observation,
            "BDI criado pela API.",
        )

        quotas = list(
            BDIQuota.objects
            .filter(bdi=bdi)
            .order_by("id")
        )

        self.assertEqual(len(quotas), 2)
        self.assertEqual(
            quotas[0].description,
            "ADMINISTRAÇÃO CENTRAL",
        )
        self.assertEqual(
            quotas[0].base,
            "CD",
        )
        self.assertEqual(
            quotas[1].description,
            "LUCRO",
        )
        self.assertEqual(
            quotas[1].percentage,
            Decimal("12.000000"),
        )

        data = response.json()

        self.assertEqual(data["id"], bdi.id)
        self.assertEqual(data["name"], "BDI Novo")
        self.assertEqual(
            len(data["quotas"]),
            2,
        )

    def test_create_bdi_returns_400_for_invalid_method(self):
        response = self.client.post(
            "/bdi",
            data={
                "name": "BDI Inválido",
                "slug": "bdi-invalido",
                "method_id": 999999,
                "observation": "",
                "quotas": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

        self.assertIn(
            "method_id",
            response.json()["details"],
        )

        self.assertFalse(
            BDI.objects.filter(
                slug="bdi-invalido"
            ).exists()
        )

    def test_create_bdi_returns_error_for_duplicate_slug(self):
        response = self.client.post(
            "/bdi",
            data={
                "name": "Outro BDI",
                "slug": self.bdi.slug,
                "method_id": self.method.id,
                "observation": "",
                "quotas": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["details"]["slug"][0],
            "Já existe um BDI com este slug.",
        )

    def test_update_bdi_replaces_quotas(self):
        response = self.client.put(
            f"/bdi/{self.bdi.id}",
            data={
                "name": "BDI Atualizado",
                "slug": "bdi-atualizado",
                "method_id": self.method.id,
                "observation": "Atualizado",
                "quotas": [
                    {
                        "group": "A",
                        "description": "ADMINISTRAÇÃO CENTRAL",
                        "percentage": "5.000000",
                        "variable": "AC",
                        "base": "CD",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        quotas = list(
            BDIQuota.objects.filter(
                bdi=self.bdi
            )
        )

        self.assertEqual(len(quotas), 1)

        self.assertEqual(
            quotas[0].percentage,
            Decimal("5.000000"),
        )

    def test_update_bdi_replaces_existing_quotas(self):

        response = self.client.put(
            f"/bdi/{self.bdi.id}",
            data={
                "name": "BDI Atualizado",
                "slug": "bdi-atualizado",
                "method_id": self.method.id,
                "observation": "Atualizado pelo PUT.",
                "quotas": [
                    {
                        "group": "A",
                        "description": "ADMINISTRAÇÃO CENTRAL",
                        "percentage": "5.000000",
                        "variable": "AC",
                        "base": "CD",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.bdi.refresh_from_db()

        self.assertEqual(
            self.bdi.name,
            "BDI Atualizado",
        )

        self.assertEqual(
            self.bdi.observation,
            "Atualizado pelo PUT.",
        )

        quotas = list(
            BDIQuota.objects
            .filter(bdi=self.bdi)
        )

        self.assertEqual(
            len(quotas),
            1,
        )

        self.assertEqual(
            quotas[0].percentage,
            Decimal("5.000000"),
        )

        self.assertEqual(
            response.json()["name"],
            "BDI Atualizado",
        )

    def test_list_bdi_methods_returns_methods_ordered_by_id(self):
        second_method = BDIMethod.objects.create(
            method="SINAPI",
        )

        response = self.client.get("/bdi/methods")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.json(),
            [
                {
                    "id": self.method.id,
                    "method": "SICRO",
                },
                {
                    "id": second_method.id,
                    "method": "SINAPI",
                },
            ],
        )