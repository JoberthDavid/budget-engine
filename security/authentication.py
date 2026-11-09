from types import SimpleNamespace

import jwt

from django.conf import settings

from rest_framework import exceptions
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)

from jwt.exceptions import InvalidTokenError, PyJWTError

from security.exceptions import AuthenticationServiceUnavailable
from security.jwks import (
    JWKSUnavailableError,
    jwks_client,
)


class ManifoldJWTAuthentication(BaseAuthentication):
    """
    Autentica requisições utilizando JWT EdDSA emitidos pelo Manifold.
    """

    REQUIRED_CLAIMS = [
        "iss",
        "sub",
        "aud",
        "scope",
        "iat",
        "exp",
        "jti",
    ]

    def authenticate(self, request):
        authorization = get_authorization_header(request).split()

        if not authorization:
            return None

        if (
            len(authorization) != 2
            or authorization[0].lower() != b"bearer"
        ):
            raise exceptions.AuthenticationFailed(
                "Cabeçalho Authorization inválido."
            )

        try:
            token = authorization[1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise exceptions.AuthenticationFailed(
                "Token de autenticação inválido."
            ) from exc

        try:
            payload = self._decode_token(token)

        except JWKSUnavailableError as exc:
            raise AuthenticationServiceUnavailable() from exc

        except InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed(
                "Token JWT inválido ou expirado."
            ) from exc

        subject = payload.get("sub")

        if (
            not isinstance(subject, str)
            or not subject.startswith("user:")
            or len(subject) <= len("user:")
        ):
            raise exceptions.AuthenticationFailed(
                "Subject do token JWT inválido."
            )

        scopes = payload.get("scope")

        if (
            not isinstance(scopes, list)
            or not all(
                isinstance(scope, str) and scope.strip()
                for scope in scopes
            )
        ):
            raise exceptions.AuthenticationFailed(
                "Scopes do token JWT inválidos."
            )

        principal = SimpleNamespace(
            is_authenticated=True,
            is_anonymous=False,
            username=subject,
            scopes=scopes,
        )

        return principal, payload

    def _decode_token(self, token):
        try:
            header = jwt.get_unverified_header(token)

        except InvalidTokenError:
            raise

        if header.get("alg") != "EdDSA":
            raise InvalidTokenError(
                "Algoritmo JWT não permitido."
            )

        kid = header.get("kid")

        if not isinstance(kid, str) or not kid:
            raise InvalidTokenError(
                "O token JWT não possui kid válido."
            )

        try:
            jwk = jwks_client.get_key(kid)

        except JWKSUnavailableError:
            raise

        except KeyError as exc:
            raise InvalidTokenError(
                "Chave de assinatura desconhecida."
            ) from exc

        try:
            public_key = jwt.PyJWK.from_dict(jwk).key

        except PyJWTError as exc:
            raise InvalidTokenError(
                "Chave pública JWKS inválida."
            ) from exc

        return jwt.decode(
            token,
            key=public_key,
            algorithms=["EdDSA"],
            audience=settings.MANIFOLD_JWT_AUDIENCE,
            issuer=settings.MANIFOLD_JWT_ISSUER,
            options={
                "require": self.REQUIRED_CLAIMS,
            },
        )

    def authenticate_header(self, request):
        return "Bearer"