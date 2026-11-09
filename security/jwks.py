import threading
import time

import requests
from django.conf import settings


class JWKSUnavailableError(Exception):
    """O serviço JWKS não está disponível ou retornou dados inválidos."""


class JWKSClient:
    CACHE_TTL_SECONDS = 300
    REQUEST_TIMEOUT_SECONDS = 5

    def __init__(self):
        self._keys = None
        self._expires_at = 0
        self._lock = threading.Lock()

    def get_keys(self):
        now = time.monotonic()

        with self._lock:
            if self._keys is not None and now < self._expires_at:
                return self._keys

            url = getattr(settings, "MANIFOLD_JWKS_URL", "")

            if not url:
                raise JWKSUnavailableError(
                    "MANIFOLD_JWKS_URL não foi configurada."
                )

            try:
                response = requests.get(
                    url,
                    timeout=self.REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                data = response.json()

            except (requests.RequestException, ValueError) as exc:
                raise JWKSUnavailableError(
                    "Não foi possível consultar o JWKS do Manifold."
                ) from exc

            keys = data.get("keys") if isinstance(data, dict) else None

            if not isinstance(keys, list) or not keys:
                raise JWKSUnavailableError(
                    "O JWKS do Manifold não contém uma lista válida de chaves."
                )

            valid_keys = [
                key
                for key in keys
                if isinstance(key, dict)
                and key.get("kty") == "OKP"
                and key.get("crv") == "Ed25519"
                and key.get("alg") == "EdDSA"
                and isinstance(key.get("kid"), str)
            ]

            if not valid_keys:
                raise JWKSUnavailableError(
                    "O JWKS não contém chaves Ed25519 compatíveis."
                )

            self._keys = valid_keys
            self._expires_at = (
                time.monotonic() + self.CACHE_TTL_SECONDS
            )

            return self._keys

    def get_key(self, kid):
        keys = self.get_keys()

        for key in keys:
            if key.get("kid") == kid:
                return key

        raise KeyError(
            f"Chave JWKS não encontrada para kid={kid}."
        )

    def clear_cache(self):
        with self._lock:
            self._keys = None
            self._expires_at = 0


jwks_client = JWKSClient()