from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.database import SessionLocal
from app.database import DATABASE_URL
from dotenv import load_dotenv
from app.models.models import UserSubscription, Users

load_dotenv()

engine = create_engine(
    DATABASE_URL
)

router = APIRouter(prefix="/user", tags=["User"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/subscription')
async def create_subscription(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.subscription:
        return {"message": "User already has a subscription", "subscription": user.subscription.plan}
    
    new_subscription = UserSubscription(
        user_id=user_id,
        plan="freemium"
    )
            
    db.add(new_subscription) 
    db.commit()
    db.refresh(new_subscription)
    return {"message": "Subscription created successfully! You are now on the freemium plan.", "subscription": new_subscription.plan}