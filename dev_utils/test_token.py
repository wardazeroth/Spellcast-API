from jose import jwt
from app.config import PRIVATE_SECRET, ID

SECRET_KEY = PRIVATE_SECRET
ID = ID

user_data ={'data': {
    "id": ID
}}

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