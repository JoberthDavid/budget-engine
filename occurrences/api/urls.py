from django.urls import path

from occurrences.api.views import (
    list_locations,
    list_suppliers,
    location_detail,
    supplier_detail,
)


urlpatterns = [
    path("suppliers", list_suppliers, name="list-suppliers"),
    path(
        "suppliers/<int:supplier_id>",
        supplier_detail,
        name="supplier-detail",
    ),
    path("locations", list_locations, name="list-locations"),
    path(
        "locations/<int:location_id>",
        location_detail,
        name="location-detail",
    ),
]