
from jose import jwt
from dotenv import load_dotenv
import os


load_dotenv() 
SECRET_KEY = os.getenv('PRIVATE_SECRET')

user_data = {
    "id": "3",
    "username": "doe",
    "email": "john_doe@gmail.com",
    "isVerified": True,
    "role": "admin",
    "profilePic": "https://example.com/avatar.jpg"
}

def crer_token(user: dict)-> str:
    return jwt.encode(user, SECRET_KEY, algorithm='HS256')

def verificar_token_sin_request(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms='HS256')
        return payload
    except Exception as e:
        print("Token inválido:", e)
        return None

if __name__ == '__main__':
    token = crer_token(user_data)
    print('token generado', token)
    
    validar = verificar_token_sin_request(token)
    print('datos usuario: ', validar)