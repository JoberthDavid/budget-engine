from django.urls import reverse
from rest_framework.test import APIClient


def test_health_route_is_registered():
    response = APIClient().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_django_routes_are_registered():
    assert reverse("health") == "/health"
    assert reverse("calculate-budget") == "/budgets/calculate"
