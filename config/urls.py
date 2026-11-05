from django.contrib import admin
from django.urls import path

from app.api.views import calculate_budget, get_bdi, health, list_bdis

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("bdi", list_bdis, name="list-bdis"),
    path("bdi/<int:bdi_id>", get_bdi, name="get-bdi"),
    path("budgets/calculate", calculate_budget, name="calculate-budget"),
]