# app/security/fernet_utils.py
import os
from cryptography.fernet import Fernet, InvalidToken

FERNET_KEY = os.environ["FERNET_KEY"]  # levántala con python-dotenv o tu config
fernet = Fernet(FERNET_KEY)

def encrypt_str(plain: str) -> str:
    return fernet.encrypt(plain.encode("utf-8")).decode("utf-8")

def decrypt_str(token: str) -> str:
    return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
