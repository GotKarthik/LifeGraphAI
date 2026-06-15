import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from core.config import settings

def _derive_dek(user_id: str) -> bytes:
    master_key = settings.ENCRYPTION_MASTER_KEY.encode('utf-8')
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"lifegraphai-salt",
        info=user_id.encode('utf-8'),
    )
    return hkdf.derive(master_key)

def encrypt_data(user_id: str, plaintext: str) -> tuple[str, str]:
    """Returns (ciphertext_b64, nonce_b64)"""
    dek = _derive_dek(user_id)
    aesgcm = AESGCM(dek)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(nonce).decode('utf-8')

def decrypt_data(user_id: str, ciphertext_b64: str, nonce_b64: str) -> str:
    dek = _derive_dek(user_id)
    aesgcm = AESGCM(dek)
    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode('utf-8')
