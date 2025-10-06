from cryptography.fernet import Fernet

# Generate a key
key = Fernet.generate_key()

# Show the key
print(key.decode())