from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.middleware import Middleware
from sqlalchemy.orm import Session, registry
from sqlalchemy import MetaData, Table, Column, Integer, String, select
from sqlalchemy import create_engine
from app.database import SessionLocal
from app.database import DATABASE_URL
from dotenv import load_dotenv
from app.models.models import AzureCredentials
from utils.fernet_utils import encrypt_str, decrypt_str

load_dotenv()

metadata= MetaData()
mapper_registry = registry()

engine = create_engine(
    DATABASE_URL
)

class Users:
    pass

tabla_usuarios= Table("users", metadata, autoload_with=engine)
mapper_registry.map_imperatively(Users, tabla_usuarios)

router = APIRouter(prefix="/user", tags=["User"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    

@router.post('/credentials')
async def create_credentianls(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    usuario= db.query(Users).filter(Users.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    body = await request.json()  # 👈 convierte bytes a dict
    azure_key = body.get('azure_key')
    region = body.get('region')
    voice = body.get('voice')
    
    encrypt_str_key = encrypt_str(azure_key)
    new_credentials = AzureCredentials(
        user_id=usuario.id,
        azure_key=encrypt_str_key,
        region=region,
        voice=voice
    )
    
    db.add(new_credentials)
    db.commit()
    db.refresh(new_credentials)
    return {"message": "Credentials created successfully"}

# @router.get('/credentials')
# async def get_credentials(request: Request, db: Session = Depends(get_db)):
#     user_id = request.state.user.get('id')
#     usuario = db.query(Users).filter(Users.id == user_id).first()
#     if not usuario:
#         raise HTTPException(status_code=404, detail="User not found")

    # return ({})