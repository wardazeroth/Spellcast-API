from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.middleware import Middleware
from sqlalchemy.orm import Session
from sqlalchemy import MetaData, Table, Column, Integer, String, select
from sqlalchemy import create_engine
from app.database import SessionLocal
from app.database import DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

metadata= MetaData()

engine = create_engine(
    DATABASE_URL
)

router = APIRouter(prefix="/accounts", tags=["Accounts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

tabla_usuarios= Table("users", metadata, autoload_with=engine)


@router.get('/')
async def validar_token(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    print('el id del user es: ', user_id)

    usuario_data = select(tabla_usuarios).where(tabla_usuarios.c.id == user_id)
    usuario = db.execute(usuario_data).mappings().first()
    print(db.execute(usuario_data))
    
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    print('y esto?', usuario)  
    userData = { 
        'id': usuario.id,
        'username': usuario.username,
        'email': usuario.email,
        'isVerified': usuario.isVerified,
        'role': usuario.role,
        'profilePic': usuario.profilePic
    } 

    return ({'userData': userData})     