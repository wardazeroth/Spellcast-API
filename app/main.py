import os
from fastapi import FastAPI
# from fastapi import FastAPI, Depends, Request
from middlewares.auth_middleware import verificar_token
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import models
from app.routers import accounts, user, tts
from fastapi.middleware.cors import CORSMiddleware
from app.redis_client import init_redis


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Define allowed origins
origins = [
    "https://spellcast.nhexa.cl",  # tu frontend
]

# Check if in development environment
if os.getenv("APP_ENV") == "development":
    # Specific origin for development to allow credentials
    origins = ["http://localhost:5173"]

else:
    # Keep existing production origins if not development
    pass  # No change needed here, as 'origins' is already defined above

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the 'origins' list here
    allow_credentials=True,           # importante si usas cookies de auth
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Origin", "X-Requested-With",
                    "Content-Type", "Accept", "Authorization"]
)


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


#Inicializar redis
@app.on_event('startup')
async def startup_event():
    init_redis()

# Incluir routers


# app.include_router(library.router)
# app.include_router(book.router)
app.include_router(accounts.router)
app.include_router(user.router)
app.include_router(tts.router)