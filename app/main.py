from fastapi import FastAPI
# from fastapi import FastAPI, Depends, Request
from middlewares.auth_middleware import verificar_token
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import models
from app.routers import library, book, accounts


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Middleware
app.middleware("http")(verificar_token)

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
app.include_router(library.router)
app.include_router(book.router)
app.include_router(accounts.router)