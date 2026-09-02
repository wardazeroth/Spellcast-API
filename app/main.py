from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middlewares.auth_middleware import authentication
from app.integrations.redis import init_redis
from app.integrations.alchemy import SessionLocal, engine
from app.routers import accounts, user, tts, subscription, storage, spell, grimoire
from app.config import APP_ENV, ALLOWED_ORIGINS_DEV
import json

app = FastAPI()

# Define allowed origins for production
origins = [
    "https://spellcast.nhexa.cl",
]

# Check if in development environment
if APP_ENV == "development":
    # Specific origin for development to allow credentials
    origins = json.loads(ALLOWED_ORIGINS_DEV)

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Origin", "X-Requested-With",
                    "Content-Type", "Accept", "Authorization"]
)

# Middleware
app.middleware("http")(authentication)

# Data base connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint
# TCORE-85: this is the API's only public, unauthenticated route (see public_routes in
# middlewares/auth_middleware.py), so it's the natural place to satisfy AGPLv3's
# network-use clause (section 13) -- license + a link to the source code, reachable by
# anyone interacting with this instance over the network, no auth required.
@app.get("/")
def root():
    return {
        "message": "Welcome to SpellCast API",
        "license": "AGPL-3.0-only",
        "license_text": "https://www.gnu.org/licenses/agpl-3.0.html",
        "source_code": "https://github.com/TerminalCore-Labs/Spellcast-API",
    }

#Starting Redis Client
@app.on_event('startup')
async def startup_event():
    init_redis()

# Routers
app.include_router(tts.router)
app.include_router(user.router)
app.include_router(grimoire.router)
app.include_router(storage.router)
app.include_router(spell.router)
app.include_router(accounts.router)
app.include_router(subscription.router)
