from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import Library
from app.integrations.alchemy import get_db

router = APIRouter(prefix="/libraries", tags=["Libraries"])

@router.get("/")
def get_libraries(db: Session = Depends(get_db)):
    return db.query(Library).all()
