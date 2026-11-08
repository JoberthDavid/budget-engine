from django.contrib import admin

from bdi.models import (
    BDIMethod,
    BDI,
    BDIQuota,
    BudgetBDI,
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


@admin.register(BudgetBDI)
class BudgetBDIAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "budget",
        "bdi",
        "created_at",
    )
    list_filter = ("bdi",)
