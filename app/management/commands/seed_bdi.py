from django.core.management.base import BaseCommand

from app.models import BDI, BDIQuota, BDIMethod


class Command(BaseCommand):
    help = "Cria ou atualiza o catálogo inicial de BDI a partir dos parâmetros atuais do eng-app."

    def handle(self, *args, **options):
        method, _ = BDIMethod.objects.update_or_create(
            method="Onerado",
            defaults={},
        )

        bdi, created = BDI.objects.update_or_create(
            slug="bdi-onerado",
            defaults={
                "name": "BDI Onerado",
                "method": method,
            },
        )

        quotas = [
            {
                "group": "BENEFÍCIOS",
                "description": "LUCRO",
                "percentage": "12.000000",
                "variable": "12,00% do CD",
                "base": BDIQuota.Base.CD,
            },
            {
                "group": "DESPESAS INDIRETAS",
                "description": "ADMINISTRAÇÃO CENTRAL",
                "percentage": "9.000000",
                "variable": "9,00% do CD",
                "base": BDIQuota.Base.CD,
            },
            {
                "group": "DESPESAS INDIRETAS",
                "description": "DESPESAS FINANCEIRAS",
                "percentage": "10.650000",
                "variable": "SELIC anual",
                "base": BDIQuota.Base.CD,
            },
            {
                "group": "DESPESAS INDIRETAS",
                "description": "RISCOS",
                "percentage": "0.500000",
                "variable": "0,50% do PV",
                "base": BDIQuota.Base.PV,
            },
            {
                "group": "DESPESAS INDIRETAS",
                "description": "SEGUROS E GARANTIAS CONTRATUAIS",
                "percentage": "0.250000",
                "variable": "0,25% do PV",
                "base": BDIQuota.Base.PV,
            },
            {
                "group": "TRIBUTOS",
                "description": "COFINS",
                "percentage": "3.000000",
                "variable": "3,00% do PV",
                "base": BDIQuota.Base.PV,
            },
            {
                "group": "TRIBUTOS",
                "description": "ISS",
                "percentage": "5.000000",
                "variable": "5,00% do PV",
                "base": BDIQuota.Base.PV,
            },
            {
                "group": "TRIBUTOS",
                "description": "PIS",
                "percentage": "0.650000",
                "variable": "0,65% do PV",
                "base": BDIQuota.Base.PV,
            },
        ]

        existing_ids = set()

        for quota_data in quotas:
            quota, _ = BDIQuota.objects.update_or_create(
                bdi=bdi,
                description=quota_data["description"],
                defaults={
                    "group": quota_data["group"],
                    "percentage": quota_data["percentage"],
                    "variable": quota_data["variable"],
                    "base": quota_data["base"],
                },
            )

            existing_ids.add(quota.id)

        (
            BDIQuota.objects
            .filter(bdi=bdi)
            .exclude(id__in=existing_ids)
            .delete()
        )

        action = "criado" if created else "atualizado"

        self.stdout.write(
            self.style.SUCCESS(
                f"BDI '{bdi.name}' {action} com {len(quotas)} quotas."
            )
        )