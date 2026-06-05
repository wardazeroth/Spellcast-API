from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models.user import Users, UserSubscription
from app.interfaces.editor import Segment
from app.integrations.fernet import decrypt_str
from app.helpers.azure import build_ssml, remove_file, build_audio_timeline, build_audio_apirest
import os, io, json, asyncio
from typing import List

router = APIRouter(prefix="/tts", tags=["tts"])

# Azure Speech SDK is not safe for concurrent use in the same process.
_azure_semaphore = asyncio.Semaphore(1)

@router.post('/')
async def text_to_speech(body: List[Segment], own_credentials: bool=True, with_timeline: bool=False, db: Session = Depends(get_db), request: Request=None):
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.subscription.plan == 'subscriber' and own_credentials==False:
        azure_api_key =os.getenv("AZURE_API_KEY")
        service_region = "brazilsouth"
    elif user.subscription.plan == 'subscriber' and own_credentials==True:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential
        azure_api_key = credentials.azure_key
        service_region = credentials.region
        azure_api_key = decrypt_str(azure_api_key)
    elif user.subscription.plan == 'freemium' and own_credentials==True:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential
        azure_api_key = credentials.azure_key
        service_region = credentials.region
        azure_api_key = decrypt_str(azure_api_key)
    else:
        raise HTTPException(status_code=403, detail="Process error. Please contact support.")

    segments = [s.dict() for s in body]

    if with_timeline:
        ssml = build_ssml(segments).strip()
        async with _azure_semaphore:
            temp_path, timeline, error, error_status = await run_in_threadpool(
                build_audio_timeline, ssml, segments, azure_api_key, service_region
            )
        if not temp_path:
            raise HTTPException(status_code=error_status or 500, detail=error or "Audio synthesis failed")
        file_stream = open(temp_path, mode='rb')
        def iterfile():
            try:
                yield from file_stream
            finally:
                file_stream.close()
                remove_file(temp_path)
    else:
        ssml = build_ssml(segments)
        audio_bytes = await build_audio_apirest(ssml=ssml, azure_api_key=azure_api_key, service_region=service_region)
        file_stream = io.BytesIO(audio_bytes)
        def iterfile():
            yield from file_stream

    headers = {"Content-Disposition": 'attachment; filename="tts.mp3"'}

    if with_timeline:
        json_timeline = json.dumps(timeline, ensure_ascii=True)
        headers["X-Timeline"] = json_timeline
        headers["Access-Control-Expose-Headers"] = "X-Timeline"

    return StreamingResponse(iterfile(), media_type='audio/mpeg', headers=headers)
