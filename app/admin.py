from django.contrib import admin

from app.models import (
    Project,
    Budget,
    BudgetDomain,
    BudgetService,
    BudgetComposition,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "source_file_uf",
        "methodology",
        "type_system",
        "monetary_base_date",
        "status",
    )
    list_filter = (
        "methodology",
        "type_system",
        "status",
        "source_file_uf",
    )
    search_fields = (
        "project__name",
        "source_file_uf",
    )


@admin.register(BudgetDomain)
class BudgetDomainAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "budget",
        "highway",
        "initial_km",
        "final_km",
        "snv",
    )
    search_fields = (
        "highway",
        "snv",
    )


@admin.register(BudgetService)
class BudgetServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "budget",
        "label",
        "code",
        "description",
        "unit",
        "quantity",
    )
    list_filter = ("budget",)
    search_fields = (
        "code",
        "description",
    )


@admin.register(BudgetComposition)
class BudgetCompositionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "budget",
        "service",
        "budget_bdi",
        "label",
        "composition_id",
        "reference_base_date",
        "factor",
    )
    list_filter = (
        "budget",
        "budget_bdi",
    )
    search_fields = (
        "composition_id",
    )
