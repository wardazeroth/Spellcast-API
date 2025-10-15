from cryptography.fernet import Fernet
from app.config import FERNET_KEY

fernet = Fernet(FERNET_KEY)

def encrypt_str(plain: str) -> str:
    return fernet.encrypt(plain.encode("utf-8")).decode("utf-8")

def decrypt_str(token: str) -> str:
    return fernet.decrypt(token.encode("utf-8")).decode("utf-8")



