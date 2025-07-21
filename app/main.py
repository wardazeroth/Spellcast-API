from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import models
from app.routers import user, library, book


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependencia para obtener sesión DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Bienvenido a Spellcast API"}

# Incluir routers
app.include_router(user.router)
app.include_router(library.router)
app.include_router(book.router)