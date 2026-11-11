from security.permissions import HasScope


class HasBDIListScope(HasScope):
    """
    Autoriza listagem e criação de BDI.
    """

    method_scopes = {
        "GET": "bdi:read",
        "POST": "bdi:create",
    }

    def has_permission(self, request, view):
        required_scope = self.method_scopes.get(request.method)

        return self.has_required_scope(
            request,
            required_scope,
        )


class HasBDIObjectScope(HasScope):
    """
    Autoriza consulta, atualização e exclusão de BDI.
    """

    method_scopes = {
        "GET": "bdi:read",
        "PUT": "bdi:update",
        "DELETE": "bdi:delete",
    }

    def has_permission(self, request, view):
        required_scope = self.method_scopes.get(request.method)

        return self.has_required_scope(
            request,
            required_scope,
        )


class HasBDIReadScope(HasScope):
    """
    Autoriza consulta dos métodos de BDI.
    """

    required_scope = "bdi:read"