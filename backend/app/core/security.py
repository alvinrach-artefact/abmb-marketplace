import hashlib
import secrets

from cryptography.fernet import Fernet

from app.core.config import settings

_fernet = Fernet(settings.api_key_encryption_key.encode())


def generate_api_key(prefix: str = "abmb_live_") -> str:
    return prefix + secrets.token_urlsafe(24)


def hash_api_key(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def encrypt_api_key(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()