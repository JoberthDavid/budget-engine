from django.urls import path

from app.api.views import calculate_budget, health


urlpatterns = [
    path("health", health, name="health"),
    path("budgets/calculate", calculate_budget, name="calculate-budget"),
]
