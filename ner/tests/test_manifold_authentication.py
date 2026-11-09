import base64
import time
from unittest.mock import Mock, patch

import jwt
import requests

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from django.test import TestCase, override_settings

from rest_framework.test import APIClient

from security.jwks import jwks_client


@override_settings(
    MANIFOLD_JWKS_URL="http://manifold.test/.well-known/jwks.json",
    MANIFOLD_JWT_ISSUER="manifold-api",
    MANIFOLD_JWT_AUDIENCE="budget-engine",
)
class ManifoldJWTAuthenticationTests(TestCase):

    KID = "test-ed25519-key"

    def setUp(self):
        self.client = APIClient()

        # Gera uma chave privada Ed25519 exclusiva para os testes.
        self.private_key = Ed25519PrivateKey.generate()

        self.public_key = self.private_key.public_key()

        self.jwks = {
            "keys": [
                self._create_jwk(self.public_key)
            ]
        }

        # Simula exclusivamente a consulta HTTP ao JWKS.
        self.jwks_patcher = patch("security.jwks.requests.get")
        self.mock_jwks_get = self.jwks_patcher.start()
        self.addCleanup(self.jwks_patcher.stop)

        response = Mock()
        response.json.return_value = self.jwks
        response.raise_for_status.return_value = None

        self.mock_jwks_get.return_value = response

        jwks_client.clear_cache()

        self.addCleanup(jwks_client.clear_cache)

    @staticmethod
    def _base64url(data):
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    def _create_jwk(self, public_key, kid=None):
        raw_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "use": "sig",
            "alg": "EdDSA",
            "kid": kid or self.KID,
            "x": self._base64url(raw_public_key),
        }

    def _create_token(
        self,
        private_key=None,
        kid=None,
        issuer="manifold-api",
        audience="budget-engine",
        subject="user:test",
        scopes=None,
        expires_at=None,
        algorithm="EdDSA",
        extra_claims=None,
    ):
        now = int(time.time())

        payload = {
            "iss": issuer,
            "sub": subject,
            "aud": audience,
            "scope": (
                scopes
                if scopes is not None
                else ["ner:stations:read"]
            ),
            "iat": now,
            "exp": (
                expires_at
                if expires_at is not None
                else now + 300
            ),
            "jti": "test-token-001",
        }

        if extra_claims:
            payload.update(extra_claims)

        headers = {
            "kid": kid or self.KID,
        }

        signing_key = private_key or self.private_key

        if algorithm == "HS256":
            signing_key = "test-secret"

        return jwt.encode(
            payload,
            signing_key,
            algorithm=algorithm,
            headers=headers,
        )

    def _get_stations(self, token=None):
        headers = {}

        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"

        return self.client.get(
            "/ner/stations",
            **headers,
        )

    def test_valid_ed25519_token_allows_access(self):
        token = self._create_token()

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        self.mock_jwks_get.assert_called_once()

    def test_missing_token_returns_401(self):
        response = self._get_stations()

        self.assertEqual(response.status_code, 401)

        self.mock_jwks_get.assert_not_called()

    def test_malformed_token_returns_401(self):
        response = self._get_stations("not-a-valid-jwt")

        self.assertEqual(response.status_code, 401)

    def test_invalid_signature_returns_401(self):
        another_private_key = Ed25519PrivateKey.generate()

        token = self._create_token(
            private_key=another_private_key,
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_wrong_issuer_returns_401(self):
        token = self._create_token(
            issuer="another-issuer",
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_wrong_audience_returns_401(self):
        token = self._create_token(
            audience="another-service",
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_expired_token_returns_401(self):
        token = self._create_token(
            expires_at=int(time.time()) - 60,
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_unknown_kid_returns_401(self):
        token = self._create_token(
            kid="unknown-key",
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_unsupported_algorithm_returns_401(self):
        token = self._create_token(
            algorithm="HS256",
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

        # O algoritmo é rejeitado antes da consulta ao JWKS.
        self.mock_jwks_get.assert_not_called()

    def test_invalid_subject_returns_401(self):
        token = self._create_token(
            subject="service:budget-engine",
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_missing_required_claim_returns_401(self):
        token = self._create_token(
            extra_claims={
                "jti": None,
            },
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_missing_scope_returns_401(self):
        token = self._create_token(
            scopes=None,
            extra_claims={
                "scope": None,
            },
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 401)

    def test_insufficient_scope_returns_403(self):
        token = self._create_token(
            scopes=["ner:calculations:create"],
        )

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 403)

    def test_jwks_unavailable_returns_503(self):
        self.mock_jwks_get.side_effect = requests.ConnectionError(
            "Manifold indisponível"
        )

        token = self._create_token()

        response = self._get_stations(token)

        self.assertEqual(response.status_code, 503)