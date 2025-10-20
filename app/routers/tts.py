from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models import Users, UserSubscription
from app.integrations.fernet import decrypt_str
from app.helpers.azure import build_ssml, remove_file
from app.config import DEFAULT_VOICE
import os, httpx
import tempfile

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post('/')
async def text_to_speech(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    body = await request.json()
    text = body.get('text')
    voice = body.get('voice')
    own_credentials = body.get('own_credentials', False)
            
    if user.subscription.plan == 'subscriber' and own_credentials==False:
        azure_api_key =os.getenv("AZURE_API_KEY")
        service_region = "brazilsouth"
    elif user.subscription.plan == 'subscriber' and own_credentials==True:
        credenciales = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().current_credential
        azure_api_key = credenciales.azure_key
        service_region = credenciales.region
        azure_api_key = decrypt_str(azure_api_key)
    elif user.subscription.plan == 'freemium' and own_credentials==True:
        credenciales = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().current_credential
        if not credenciales:
            raise HTTPException(status_code=400, detail="No Azure credentials found for this user")
        azure_api_key = credenciales.azure_key
        service_region = credenciales.region
        azure_api_key = decrypt_str(azure_api_key)
    else:
        raise HTTPException(status_code=403, detail="Process error. Please contact support.")

    endpoint = f"https://{service_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
        "Ocp-Apim-Subscription-Key": azure_api_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
        "User-Agent": "fastapi-tts"
    }
    
    ssml = build_ssml(text, voice or DEFAULT_VOICE)
    
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(endpoint, headers= headers, content=ssml)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail= response.text)
    
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tmp_file.write(response.content)
    tmp_file.flush()
    tmp_file.close()

    file_stream = open(tmp_file.name, mode='rb')
    
    def iterfile():
        try:
            yield from file_stream
        finally: 
            file_stream.close()
            remove_file(tmp_file.name)
    
    return StreamingResponse(  
        iterfile(), media_type='audio/mpeg',
        headers={"Content-Disposition": 'attachment; filename="tts.mp3"'}
    )
    
