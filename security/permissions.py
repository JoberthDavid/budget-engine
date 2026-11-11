from rest_framework.permissions import BasePermission


class HasScope(BasePermission):
    """
    Permissão genérica baseada nos scopes presentes no JWT.

    As classes específicas devem definir required_scope
    ou implementar sua própria seleção de escopo.
    """

    required_scope = None

    message = "O token não possui autorização para esta operação."

    def has_permission(self, request, view):
        return self.has_required_scope(
            request,
            self.required_scope,
        )

    def has_required_scope(self, request, required_scope):
        if not request.user or not request.user.is_authenticated:
            return False

        if not isinstance(request.auth, dict):
            return False

        scopes = request.auth.get("scope")

        if not isinstance(scopes, list):
            return False

        if not required_scope:
            return False

        return required_scope in scopes