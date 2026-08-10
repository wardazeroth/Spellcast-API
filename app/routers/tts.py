from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models.user import Users, UserSubscription, Credential
from app.interfaces.editor import Node, SimpleTTSRequest, TTSmarks, TTAttrs
from app.integrations.fernet import decrypt_str
from app.helpers.builder_azure import azure_time_builder, azure_ssml_build
from app.helpers.builder_aws import aws_ssml_build, aws_timeline_builder
from app.utils.parser import parser_nodes
from app.config import AZURE_API_KEY
from app.misc.consts import DEFAULT_VOICES
from typing import Union
import io, json

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post('/')
async def text_to_speech(body: Union[Node, SimpleTTSRequest], own_credentials: bool=True, with_timeline: bool=False, db: Session = Depends(get_db), request: Request=None): 
    user_id = request.state.user.get('id')
    user= db.query(Users).filter(Users.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.subscription.plan == 'subscriber' and not own_credentials:
        config_dict = {
            'apiKey' : AZURE_API_KEY,
            'region' : "brazilsouth"
        }
        provider = 'azure'
        return await azure_synthesis(config_dict, provider, body, with_timeline)

    elif user.subscription.plan == 'subscriber' and own_credentials:
        credentials = db.query(Credential).join(UserSubscription, UserSubscription.current_credential==Credential.id).filter(UserSubscription.user_id==user_id).first()
        config_dict = json.loads(decrypt_str(credentials.config))
        provider = credentials.provider_type
        if provider == 'azure':
            return await azure_synthesis(config_dict, provider, body, with_timeline)

        elif provider == 'aws':
            return await aws_synthesis(config_dict, provider, body, with_timeline)

    elif user.subscription.plan == 'freemium' and own_credentials:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential
        config_dict = json.loads(decrypt_str(credentials.config))
        provider = credentials.provider_type
        if credentials.provider_type == 'azure':
            return await azure_synthesis(config_dict, provider, body, with_timeline)
        
        elif credentials.provider_type == 'aws':
            return await aws_synthesis(config_dict, provider, body, with_timeline)   
    else:
        raise HTTPException(status_code=403, detail="Process error. Please contact support.")

def body_type_request(body, provider):
    if isinstance(body, SimpleTTSRequest):
        selected_voice = body.voice if body.voice is not None else DEFAULT_VOICES.get(provider)
        node_tree = Node(
            type="text",
            text=body.text,
            marks=[
                TTSmarks(
                    type="tts",
                    attrs=TTAttrs(voice=selected_voice, inflection=body.inflection)
                )
            ]
        )
    else:
        node_tree = body
    return node_tree
            
async def azure_synthesis(config_dict, provider, body, with_timeline):
    api_key = config_dict.get('apiKey')
    service_region = config_dict.get('region')

    node_tree = body_type_request(body, provider)
    segments = parser_nodes(node_tree)
    if with_timeline:
        return await azure_time_builder(segments, api_key, service_region)
    else:
        return await azure_ssml_build(segments, api_key, service_region)

async def aws_synthesis(config_dict, provider, body, with_timeline):
    access_api_key = config_dict.get('accessKeyId')
    secret_access_key = config_dict.get('secretAccessKey')
    region = config_dict.get('region')

    node_tree = body_type_request(body, provider)
    segments = parser_nodes(node_tree)
    voice_id=segments[0]['voice']
    if with_timeline:
        return await aws_timeline_builder(segments, voice_id, access_api_key, secret_access_key, region)
    else:
        return await aws_ssml_build(voice_id, segments, access_api_key, secret_access_key, region)
    