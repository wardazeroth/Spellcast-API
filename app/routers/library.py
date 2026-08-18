from sqlalchemy.orm import Session
from app.models.library import Library, SpellLibrary
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
    spell_id = body.get('spell_id')

    # Library.user_id is unique — reuse the existing row for this user instead of
    # crashing on a duplicate-key insert (Library itself has no spell_id column;
    # the spell/library association lives in the SpellLibrary junction table).
    library = db.query(Library).filter(Library.user_id == user_id).first()
    if not library:
        library = Library(user_id=user_id)
        db.add(library)
        db.commit()
        db.refresh(library)

    if spell_id:
        spell_library = SpellLibrary(
            spell_id = spell_id,
            library_id = library.id
        )
        db.add(spell_library)
        db.commit()

    return()

@router.get("/")
def get_libraries(db: Session = Depends(get_db)):
    return db.query(Library).all()
