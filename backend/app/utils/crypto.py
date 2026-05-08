"""AES-256-GCM encrypt/decrypt helpers shared across the application.

Key derivation and ciphertext format must remain stable so that existing
rows in ``tb_expert_settings.ssb_password_enc`` stay decryptable.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config.settings import settings

_AES_KEY_BYTES = 32


def _derive_key() -> bytes:
    """Derive a 32-byte key from settings.aes_key (repeating-byte pattern)."""
    raw = settings.aes_key.encode("utf-8")
    return (raw * (_AES_KEY_BYTES // len(raw) + 1))[:_AES_KEY_BYTES]


def encrypt(plaintext: str) -> str:
    """AES-256-GCM encrypt; returns base64-encoded nonce+ciphertext."""
    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt(token: str | None) -> str | None:
    """Decrypt base64-encoded nonce+ciphertext; returns plain text.

    Returns ``None`` if *token* is ``None`` or empty string.
    """
    if token is None or token == "":
        return None
    key = _derive_key()
    aesgcm = AESGCM(key)
    data = base64.b64decode(token)
    nonce, ciphertext = data[:12], data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
