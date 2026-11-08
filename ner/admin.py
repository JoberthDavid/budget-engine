from django.contrib import admin

from ner.models import (
    PluviometricStation,
    MowingWorkloadLocation,
    MowingWorkloadCalculation,
    MowingWorkloadCalculationStation,
    BudgetMowingWorkload,
)


@admin.register(PluviometricStation)
class PluviometricStationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "code",
        "name",
        "municipality",
        "state",
        "operator",
        "nere",
    )

    list_filter = (
        "state",
        "operator",
    )

    search_fields = (
        "code",
        "name",
        "municipality",
        "operator",
    )

    ordering = (
        "state",
        "municipality",
        "code",
    )

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "code",
                    "name",
                    "operator",
                )
            },
        ),
        (
            "Localização",
            {
                "fields": (
                    "municipality",
                    "state",
                    "latitude",
                    "longitude",
                )
            },
        ),
        (
            "Dados técnicos",
            {
                "fields": (
                    "nd",
                    "nere",
                    "norm_reference",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


@admin.register(MowingWorkloadLocation)
class MowingWorkloadLocationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "latitude",
        "longitude",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "name",
        "id",
    )

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "name",
                    "description",
                )
            },
        ),
        (
            "Coordenadas geográficas",
            {
                "fields": (
                    "latitude",
                    "longitude",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


class MowingWorkloadCalculationStationInline(admin.TabularInline):

    model = MowingWorkloadCalculationStation
    extra = 0
    can_delete = False

    fields = (
        "sequence",
        "station_code_snapshot",
        "station_name_snapshot",
        "latitude_snapshot",
        "longitude_snapshot",
        "distance_km",
        "weight",
        "nere_snapshot",
        "weighted_nere",
        "nd_snapshot",
    )

    readonly_fields = fields

    ordering = ("sequence",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MowingWorkloadCalculation)
class MowingWorkloadCalculationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "location",
        "station_count",
        "weighted_nere",
        "nerp",
        "adjustment",
        "ner",
        "calculated_at",
    )

    list_filter = (
        "ner",
        "nerp",
        "adjustment",
        "calculation_method",
    )

    search_fields = (
        "location__name",
        "location__description",
    )

    ordering = ("-calculated_at",)

    inlines = [
        MowingWorkloadCalculationStationInline,
    ]

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "location",
                    "calculation_method",
                    "norm_reference",
                    "calculated_at",
                )
            },
        ),
        (
            "Parâmetros",
            {
                "fields": (
                    "station_count",
                    "adjustment",
                )
            },
        ),
        (
            "Resultados",
            {
                "fields": (
                    "weighted_nere",
                    "nerp",
                    "ner",
                )
            },
        ),
        (
            "Memória de cálculo",
            {
                "fields": (
                    "sum_weighted_nere",
                    "sum_weights",
                )
            },
        ),
    )

    readonly_fields = (
        "location",
        "calculation_method",
        "norm_reference",
        "calculated_at",
        "station_count",
        "adjustment",
        "weighted_nere",
        "nerp",
        "ner",
        "sum_weighted_nere",
        "sum_weights",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in ("GET", "HEAD")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MowingWorkloadCalculationStation)
class MowingWorkloadCalculationStationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "calculation",
        "sequence",
        "station_code_snapshot",
        "station_name_snapshot",
        "distance_km",
        "weight",
        "nere_snapshot",
        "weighted_nere",
    )

    list_filter = (
        "calculation__ner",
        "calculation__calculation_method",
    )

    search_fields = (
        "station_code_snapshot",
        "station_name_snapshot",
        "station__code",
        "station__name",
    )

    ordering = (
        "-calculation__calculated_at",
        "sequence",
    )

    readonly_fields = (
        "calculation",
        "station",
        "sequence",
        "distance_km",
        "weight",
        "weighted_nere",
        "station_code_snapshot",
        "station_name_snapshot",
        "latitude_snapshot",
        "longitude_snapshot",
        "nere_snapshot",
        "nd_snapshot",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in ("GET", "HEAD")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BudgetMowingWorkload)
class BudgetMowingWorkloadAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "budget",
        "location",
        "calculation",
        "created_at",
    )

    search_fields = (
        "budget__project__name",
        "location__name",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    list_select_related = (
        "budget",
        "location",
        "calculation",
    )
