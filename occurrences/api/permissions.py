from security.permissions import HasScope


class HasSupplierListScope(HasScope):
    method_scopes = {
        "GET": "occurrences:suppliers:read",
        "POST": "occurrences:suppliers:create",
    }

    def has_permission(self, request, view):
        return self.has_required_scope(
            request,
            self.method_scopes.get(request.method),
        )


class HasSupplierObjectScope(HasScope):
    method_scopes = {
        "GET": "occurrences:suppliers:read",
        "PUT": "occurrences:suppliers:update",
        "PATCH": "occurrences:suppliers:update",
        "DELETE": "occurrences:suppliers:delete",
    }

    def has_permission(self, request, view):
        return self.has_required_scope(
            request,
            self.method_scopes.get(request.method),
        )


class HasLocationListScope(HasScope):
    method_scopes = {
        "GET": "occurrences:locations:read",
        "POST": "occurrences:locations:create",
    }

    def has_permission(self, request, view):
        return self.has_required_scope(
            request,
            self.method_scopes.get(request.method),
        )


class HasLocationObjectScope(HasScope):
    method_scopes = {
        "GET": "occurrences:locations:read",
        "PUT": "occurrences:locations:update",
        "PATCH": "occurrences:locations:update",
        "DELETE": "occurrences:locations:delete",
    }

    def has_permission(self, request, view):
        return self.has_required_scope(
            request,
            self.method_scopes.get(request.method),
        )