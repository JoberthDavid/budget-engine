from rest_framework.exceptions import APIException


class AuthenticationServiceUnavailable(APIException):
    status_code = 503
    default_detail = (
        "O serviço de autenticação do Manifold está temporariamente "
        "indisponível."
    )
    default_code = "authentication_service_unavailable"