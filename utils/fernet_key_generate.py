from cryptography.fernet import Fernet

# Generar una nueva clave
key = Fernet.generate_key()

# Mostrarla
print(key.decode())