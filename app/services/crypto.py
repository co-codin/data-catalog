import os
import base64
import logging

from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


logger = logging.getLogger(__name__)


def load_key(path: str, file_name: str) -> bytes:
    os.makedirs(path, exist_ok=True)
    private_key_path = os.path.join(path, file_name)

    if os.path.exists(private_key_path):
        with open(private_key_path, 'rb') as fd:
            key = base64.b64decode(fd.read())
    else:
        key = AESGCM.generate_key(bit_length=256)
        with open(private_key_path, 'wb') as fd:
            fd.write(base64.b64encode(key))

        os.chmod(path, 0o400)
        os.chmod(private_key_path, 0o400)
    return key


def encrypt(key: bytes, data: bytes) -> bytes:
    nonce = os.urandom(12)
    aad = os.urandom(16)
    encrypted = nonce + AESGCM(key).encrypt(nonce, data, aad) + aad
    return base64.b64encode(encrypted)


def decrypt(key: bytes, data: bytes) -> Optional[bytes]:
    data = base64.b64decode(data)
    nonce = data[:12]
    aad = data[-16:]
    encrypted = data[12:-16]
    try:
        decrypted = AESGCM(key).decrypt(nonce, encrypted, aad)
    except Exception as err:
        logger.warning(str(err))
        decrypted = None
    return decrypted
