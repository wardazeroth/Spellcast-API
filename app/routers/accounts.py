from fastapi import APIRouter, Depends, Request, HTTPException
from app.models.models import User, Book
from fastapi.middleware import Middleware
from app.database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/accounts", tags=["Accounts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/')
async def validar_token(request: Request, db: Session= Depends(get_db)):
    user_id = request.state.user.get('id')
    print('el id del user es: ', user_id)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    userData = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'isVerified': '',
        'role': '',
        'profilePic': ''
    }

    return ({'userData': userData})