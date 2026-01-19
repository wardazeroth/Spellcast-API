from sqlalchemy.orm import Session
from app.models.library import Library
from app.models.user import Users
from fastapi import APIRouter, Depends, Request, HTTPException
from app.integrations.alchemy import get_db

router = APIRouter(prefix="/libraries", tags=["Libraries"])

@router.post("/")
async def create_library(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")    
    
    body = await request.json()
    document_id = body.get('document_id')


    new_library = Library(
        user_id = user_id,
        document_id = document_id
    )

    db.add(new_library) 
    db.commit()
    db.refresh(new_library)
    return()

@router.get("/")
def get_libraries(db: Session = Depends(get_db)):
    return db.query(Library).all()
