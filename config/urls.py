from django.contrib import admin
from django.urls import path

from app.api.views import calculate_budget, health
from bdi.api.views import (
    get_bdi,
    list_bdis,
    list_bdi_methods,
)
from ner.api.views import (
    create_ner_calculation,
    list_ner_stations,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("bdi", list_bdis, name="list-bdis"),
    path("bdi/methods", list_bdi_methods, name="list-bdi-methods"),
    path("bdi/<int:bdi_id>", get_bdi, name="get-bdi"),
    path("budgets/calculate", calculate_budget, name="calculate-budget"),
    path("ner/stations", list_ner_stations, name="list-ner-stations"),
    path("ner/calculations", create_ner_calculation, name="create-ner-calculation"),
]
