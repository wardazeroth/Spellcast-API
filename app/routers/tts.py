from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models.user import Users, UserSubscription, Credential
from app.interfaces.editor import Segment
from app.integrations.fernet import decrypt_str
from app.helpers.builder_azure import azure_time_builder, azure_ssml_build
from app.helpers.builder_aws import aws_ssml_build, aws_timeline_builder
from app.config import AZURE_API_KEY
from typing import List
import json

router = APIRouter(prefix="/tts", tags=["tts"])


# Bridge (TCORE-49): keeps main's flat `List[Segment]` request contract (from PR #55/#57)
# while adopting the credential refactor's multi-provider dispatch. The client still POSTs a
# list of segments; the credential's provider_type decides which builder runs. The builders
# (builder_azure/builder_aws) already consume the segment list directly, so no Node parsing
# is needed here.
@router.post('/')
async def text_to_speech(body: List[Segment], own_credentials: bool = True, with_timeline: bool = False, db: Session = Depends(get_db), request: Request = None):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    segments = [s.dict() for s in body]

    # Subscriber without own credentials → platform Azure key.
    if user.subscription.plan == 'subscriber' and not own_credentials:
        config_dict = {'apiKey': AZURE_API_KEY, 'region': "brazilsouth"}
        return await azure_synthesis(config_dict, segments, with_timeline)

    # Subscriber or freemium using their own credential → dispatch by provider_type.
    if user.subscription.plan in ('subscriber', 'freemium') and own_credentials:
        credentials = (
            db.query(Credential)
            .join(UserSubscription, UserSubscription.current_credential == Credential.id)
            .filter(UserSubscription.user_id == user_id)
            .first()
        )
        if not credentials:
            raise HTTPException(status_code=404, detail="No active credential found")

        config_dict = json.loads(decrypt_str(credentials.config))
        provider = credentials.provider_type

        if provider == 'azure':
            return await azure_synthesis(config_dict, segments, with_timeline)
        elif provider == 'aws':
            return await aws_synthesis(config_dict, segments, with_timeline)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    raise HTTPException(status_code=403, detail="Process error. Please contact support.")


async def azure_synthesis(config_dict, segments, with_timeline):
    api_key = config_dict.get('apiKey')
    service_region = config_dict.get('region')
    if with_timeline:
        return await azure_time_builder(segments, api_key, service_region)
    return await azure_ssml_build(segments, api_key, service_region)


async def aws_synthesis(config_dict, segments, with_timeline):
    access_api_key = config_dict.get('accessKeyId')
    secret_access_key = config_dict.get('secretAccessKey')
    region = config_dict.get('region')
    voice_id = segments[0]['voice'] if segments else None
    if with_timeline:
        return await aws_timeline_builder(segments, voice_id, access_api_key, secret_access_key, region)
    return await aws_ssml_build(voice_id, segments, access_api_key, secret_access_key, region)
