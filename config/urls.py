from django.urls import path

from app.api.views import calculate_budget, health, list_bdis


urlpatterns = [
    path("health", health, name="health"),
    path("bdi", list_bdis, name="list-bdis"),
    path("budgets/calculate", calculate_budget, name="calculate-budget"),
]
