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
    PluviometricStation,
    MowingWorkloadLocation,
    MowingWorkloadCalculation,
    MowingWorkloadCalculationStation,
    BudgetMowingWorkload,
)


# ============================================================
# BDI
# ============================================================

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


# ============================================================
# PROJECT
# ============================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "updated_at")
    search_fields = ("name",)


# ============================================================
# BUDGET
# ============================================================

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


# ============================================================
# NER - ESTAÇÕES PLUVIOMÉTRICAS
# ============================================================

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

# ============================================================
# NER - LOCALIZAÇÕES
# ============================================================

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


# ============================================================
# NER - ESTAÇÕES UTILIZADAS NO CÁLCULO
# ============================================================

class MowingWorkloadCalculationStationInline(
    admin.TabularInline
):

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

    ordering = (
        "sequence",
    )

    def has_add_permission(self, request, obj=None):
        return False


# ============================================================
# NER - HISTÓRICO DE CÁLCULOS
# ============================================================

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

    ordering = (
        "-calculated_at",
    )

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


# ============================================================
# NER - REGISTROS INDIVIDUAIS DAS ESTAÇÕES
# ============================================================

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


# ============================================================
# NER - ASSOCIAÇÃO COM ORÇAMENTOS
# ============================================================

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

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )

    list_select_related = (
        "budget",
        "location",
        "calculation",
    )