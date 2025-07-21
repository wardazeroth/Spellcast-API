from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import Library

router = APIRouter(prefix="/libraries", tags=["Libraries"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_libraries(db: Session = Depends(get_db)):
    return db.query(Library).all()
