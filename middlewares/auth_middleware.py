from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt, JWTError 
import os
from dotenv import load_dotenv      

load_dotenv()
SECRET_KEY= os.getenv("PRIVATE_SECRET")
ALGORITHM = os.getenv('ALGORITHM')

async def verificar_token(request: Request, call_next):
    
    rutas_publicas = ["/", "/favicon.ico", '/docs',"/openapi.json"]

    if request.url.path in rutas_publicas:
        return await call_next(request)
    
    token = request.cookies.get('userToken') 
    print("Token recibido:", token) 
    if not token:
        raise HTTPException(status_code=401, detail='Token no proporcionado')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload.get('data') 
        
    except JWTError:
        raise HTTPException(status_code=401, detail='Token no es válido o ya expiró')
    response = await call_next(request)
    return response

