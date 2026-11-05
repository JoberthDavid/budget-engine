from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from app.models import BDI, BDIQuota, BDIMethod


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