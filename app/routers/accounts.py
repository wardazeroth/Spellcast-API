from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.middleware import Middleware
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Users
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.get('/')
async def validar_token(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    print('el id del user es: ', user_id)

    usuario= db.query(Users).filter(Users.id == user_id).first()
    print(usuario)

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