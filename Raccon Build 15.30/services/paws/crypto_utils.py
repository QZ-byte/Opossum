from cryptography.fernet import Fernet
import base64, hashlib

def derive_key(master_password: str) -> bytes:
    """Из мастер-пароля делаем ключ для Fernet (через SHA256)."""
    digest = hashlib.sha256(master_password.encode()).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_password(master_password: str, plain: str) -> str:
    key = derive_key(master_password)
    f = Fernet(key)
    return f.encrypt(plain.encode()).decode()

def decrypt_password(master_password: str, token: str) -> str:
    key = derive_key(master_password)
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()
