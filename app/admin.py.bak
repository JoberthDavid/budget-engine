from django.contrib import admin

from app.models import (
    BDI,
    BDIMethod,
    BDIQuota,
    Budget,
    BudgetBDI,
    BudgetComposition,
    BudgetDomain,
    BudgetService,
    Project,
)


class BDIQuotaInline(admin.TabularInline):
    model = BDIQuota
    extra = 0


@admin.register(BDIMethod)
class BDIMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "method")
    search_fields = ("method",)


@admin.register(BDI)
class BDIAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "method")
    list_filter = ("method",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BDIQuotaInline]


@admin.register(BDIQuota)
class BDIQuotaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bdi",
        "group",
        "description",
        "percentage",
        "variable",
    )
    list_filter = ("group", "bdi")
    search_fields = (
        "description",
        "variable",
        "bdi__name",
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


@admin.register(BudgetBDI)
class BudgetBDIAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "budget",
        "bdi",
        "created_at",
    )
    list_filter = ("bdi",)


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