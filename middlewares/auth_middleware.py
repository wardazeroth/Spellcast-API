from fastapi import Request, HTTPException
from jose import jwt, JWTError 
from app.config import PRIVATE_SECRET, ALGORITHM    

SECRET_KEY= PRIVATE_SECRET   
ALGORITHM = ALGORITHM

async def authentication(request: Request, call_next):

    if request.method == "OPTIONS":
        return await call_next(request)

    public_routes = ["/", "/favicon.ico", '/docs', "/openapi.json"]

    if request.url.path in public_routes:
        return await call_next(request)

    token = request.cookies.get('userToken')
    if not token:
        raise HTTPException(status_code=401, detail='Token not provided')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload.get('data')

    except JWTError:
        raise HTTPException(status_code=401, detail='Token is not valid or has expired')
    response = await call_next(request)
    return response

