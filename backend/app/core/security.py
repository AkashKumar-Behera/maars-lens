import os
from typing import Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings

NONCE_LENGTH = 12  # Standard recommended IV length for AES-GCM (96 bits)
TAG_LENGTH = 16    # Standard GCM authentication tag length (128 bits)


def get_aesgcm(key: Optional[bytes] = None) -> AESGCM:
    """
    Returns an AESGCM cipher instance.
    Uses provided 256-bit (32-byte) key or parses settings.ENCRYPTION_KEY hex.
    """
    if key is None:
        key = bytes.fromhex(settings.ENCRYPTION_KEY)
    if len(key) not in (16, 24, 32):
        raise ValueError(f"AES key must be 128, 192, or 256 bits (16, 24, or 32 bytes). Got {len(key)} bytes.")
    return AESGCM(key)


def encrypt_data(data: Union[str, bytes], key: Optional[bytes] = None) -> bytes:
    """
    Encrypts a string or bytes using AES-256-GCM.
    Returns: 12-byte nonce prepended to the ciphertext and auth tag:
             `nonce (12 bytes) + ciphertext + tag (16 bytes)`
    """
    aesgcm = get_aesgcm(key)
    nonce = os.urandom(NONCE_LENGTH)
    payload = data.encode("utf-8") if isinstance(data, str) else data
    ciphertext = aesgcm.encrypt(nonce, payload, None)
    return nonce + ciphertext


def decrypt_data(encrypted_data: bytes, key: Optional[bytes] = None) -> str:
    """
    Decrypts an AES-256-GCM encrypted payload and returns UTF-8 string.
    Expects format: `nonce (12 bytes) + ciphertext + tag (16 bytes)`.
    """
    decrypted_bytes = decrypt_bytes(encrypted_data, key)
    return decrypted_bytes.decode("utf-8")


def decrypt_bytes(encrypted_data: bytes, key: Optional[bytes] = None) -> bytes:
    """
    Decrypts an AES-256-GCM encrypted payload and returns raw decrypted bytes.
    Expects format: `nonce (12 bytes) + ciphertext + tag (16 bytes)`.
    """
    if len(encrypted_data) < (NONCE_LENGTH + TAG_LENGTH):
        raise ValueError("Encrypted data is too short to contain nonce and authentication tag.")

    aesgcm = get_aesgcm(key)
    nonce = encrypted_data[:NONCE_LENGTH]
    ciphertext = encrypted_data[NONCE_LENGTH:]
    return aesgcm.decrypt(nonce, ciphertext, None)
