from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.library import Document
from app.integrations.alchemy import get_db
from fastapi import APIRouter, Depends, Request, HTTPException
from app.models.user import Users
from uuid import uuid4
from app.integrations.boto3 import generate_presigned_url

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/")
def get_documents(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")   
     
    return db.query(Document).all()

@router.post("/")
async def create_document(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")    
    
    body = await request.json()
    name = body.get('name')
    type = body.get('type')

    key = f"{type}/{uuid4()}-{name}"
    try:
        url = generate_presigned_url(key, content_type=type)
        new_document = Document(
            name = name,
            type = type,
            file_path = url
        )

        db.add(new_document) 
        db.commit()
        db.refresh(new_document)
        return()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))