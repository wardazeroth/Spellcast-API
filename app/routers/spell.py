from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.grimoire import Grimoire, SpellGrimoire
from app.models.spell import Spell
from app.integrations.alchemy import get_db
from fastapi import APIRouter, Depends, Request, HTTPException
from app.models.user import Users
from uuid import uuid4
from app.integrations.boto3 import generate_presigned_url
from app.config import AWS_S3_BUCKET

router = APIRouter(prefix="/spells", tags=["spells"])

@router.get("/")
def get_spells(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    grimoire = db.query(Grimoire).filter(Grimoire.user_id == user_id).first()
    if not grimoire:
        return []
    spell_grimoire = db.query(SpellGrimoire).filter(SpellGrimoire.grimoire_id == grimoire.id).all() 

    return db.query(Spell).filter(Spell.id.in_([spell.spell_id for spell in spell_grimoire])).all()

@router.post("/")
async def create_spell(request: Request, db: Session = Depends(get_db)):
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
        new_spell = Spell(
            name = name,
            type = type,
            file_path = f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{key}",
            visibility = "private",
            review_status = "none",
        )

        db.add(new_spell)
        db.commit()
        db.refresh(new_spell)
        return({'spell': new_spell,'uploadUrl': url})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{spell_id}/transcription")
async def transcription(spell_id: str, request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    spell = db.query(Spell).filter(
    Spell.id == spell_id).first()

    if not spell:
        raise HTTPException(status_code=404, detail="Spell doesn't exist")

    grimoire = db.query(Grimoire).filter(Grimoire.user_id == user_id).first()
    if grimoire: 
        spell_grimoire = db.query(SpellGrimoire).filter(SpellGrimoire.grimoire_id == grimoire.id, SpellGrimoire.spell_id == spell.id).first()
    else:
        pass
    if not spell.visibility == 'public' and spell.review_status == 'approved':
        pass
    elif not spell_grimoire:
        pass
    else:
        raise HTTPException(status_code=403, detail="")
