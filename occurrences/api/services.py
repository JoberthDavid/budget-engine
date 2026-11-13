from django.db import transaction

from occurrences.models import (
    SupplierLocationMaterial,
    SupplierLocationMaterialNature,
)


@transaction.atomic
def save_supplier_location(serializer, *, replace=False):
    """
    Persiste uma unidade fornecedora e sincroniza suas relações.

    Args:
        serializer: SupplierLocationSerializer validado.
        replace: Quando True, aplica semântica de substituição (PUT).
                 Quando False, preserva relações omitidas (PATCH).

    Returns:
        SupplierLocation persistida.
    """
    validated_data = serializer.validated_data

    nature_ids = validated_data.pop("nature_ids", None)
    material_ids = validated_data.pop("material_ids", None)

    location = serializer.save()

    if nature_ids is not None:
        sync_location_natures(location, nature_ids)

    elif replace:
        sync_location_natures(location, [])

    if material_ids is not None:
        sync_location_materials(location, material_ids)

    elif replace:
        sync_location_materials(location, [])

    return location


def sync_location_natures(location, nature_ids):
    """
    Substitui integralmente as naturezas associadas à unidade.
    """
    SupplierLocationMaterialNature.objects.filter(
        supplier_location=location,
    ).exclude(
        material_nature_id__in=nature_ids,
    ).delete()

    existing_ids = set(
        SupplierLocationMaterialNature.objects.filter(
            supplier_location=location,
            material_nature_id__in=nature_ids,
        ).values_list("material_nature_id", flat=True)
    )

    new_links = [
        SupplierLocationMaterialNature(
            supplier_location=location,
            material_nature_id=nature_id,
        )
        for nature_id in nature_ids
        if nature_id not in existing_ids
    ]

    if new_links:
        SupplierLocationMaterialNature.objects.bulk_create(new_links)


def sync_location_materials(location, material_ids):
    """
    Sincroniza materiais por ativação e desativação lógica.
    """
    SupplierLocationMaterial.objects.filter(
        supplier_location=location,
    ).exclude(
        material_id__in=material_ids,
    ).update(active=False)

    existing_links = {
        link.material_id: link
        for link in SupplierLocationMaterial.objects.filter(
            supplier_location=location,
            material_id__in=material_ids,
        )
    }

    new_links = []

    for material_id in material_ids:
        link = existing_links.get(material_id)

        if link:
            if not link.active:
                link.active = True
                link.save(update_fields=["active"])
        else:
            new_links.append(
                SupplierLocationMaterial(
                    supplier_location=location,
                    material_id=material_id,
                    active=True,
                )
            )

    if new_links:
        SupplierLocationMaterial.objects.bulk_create(new_links)