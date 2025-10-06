from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.integrations.alchemy import SessionLocal
from app.models.models import Book

router = APIRouter(prefix="/books", tags=["Books"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_books(db: Session = Depends(get_db)):
    return db.query(Book).all()
