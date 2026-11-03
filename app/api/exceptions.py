from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None or response.status_code != 400:
        return response

    details = exc.detail if isinstance(exc, APIException) else response.data
    return Response(
        {
            "code": "INVALID_REQUEST",
            "message": "A requisição contém dados inválidos.",
            "details": details,
        },
        status=400,
    )
