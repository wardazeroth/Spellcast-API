from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import Book
from app.integrations.alchemy import get_db

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/")
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()
