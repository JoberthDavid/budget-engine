from django.db import transaction

from bdi.models import (
    BDI,
    BDIQuota,
    BDIMethod,
    BudgetBDI,
)


class BDIInUseError(Exception):
    pass


class BDIService:

    @staticmethod
    def _load(bdi_id):

        return (
            BDI.objects
            .select_related("method")
            .prefetch_related("quotas")
            .get(pk=bdi_id)
        )

    @staticmethod
    @transaction.atomic
    def create(data):

        method = BDIMethod.objects.get(
            pk=data["method_id"]
        )

        bdi = BDI.objects.create(
            name=data["name"],
            slug=data["slug"],
            method=method,
            observation=data.get("observation", ""),
        )

        BDIQuota.objects.bulk_create([
            BDIQuota(
                bdi=bdi,
                group=quota["group"],
                description=quota["description"],
                percentage=quota["percentage"],
                variable=quota["variable"],
                base=quota["base"],
            )
            for quota in data["quotas"]
        ])

        return BDIService._load(bdi.pk)

    @staticmethod
    @transaction.atomic
    def update(bdi_id, data):

        bdi = (
            BDI.objects
            .select_for_update()
            .get(pk=bdi_id)
        )

        method = BDIMethod.objects.get(
            pk=data["method_id"]
        )

        bdi.name = data["name"]
        bdi.slug = data["slug"]
        bdi.method = method
        bdi.observation = data.get("observation", "")

        bdi.save()

        BDIQuota.objects.filter(
            bdi=bdi
        ).delete()

        BDIQuota.objects.bulk_create([
            BDIQuota(
                bdi=bdi,
                group=quota["group"],
                description=quota["description"],
                percentage=quota["percentage"],
                variable=quota["variable"],
                base=quota["base"],
            )
            for quota in data["quotas"]
        ])

        return BDIService._load(bdi.pk)

    @staticmethod
    @transaction.atomic
    def delete(bdi_id):

        bdi = (
            BDI.objects
            .select_for_update()
            .get(pk=bdi_id)
        )

        if BudgetBDI.objects.filter(
            bdi=bdi
        ).exists():

            raise BDIInUseError

        bdi.delete()