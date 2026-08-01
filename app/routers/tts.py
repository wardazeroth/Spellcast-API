from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.integrations.alchemy import get_db
from app.models.user import Users, UserSubscription
from app.interfaces.editor import Node, SimpleTTSRequest, TTSmarks, TTAttrs
from app.integrations.fernet import decrypt_str
from app.helpers.builder_azure import timeline_builder, ssml_build
from app.helpers.builder_aws import aws_ssml_build
from app.utils.parser import parser_nodes
from app.config import AZURE_API_KEY
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
        api_key = AZURE_API_KEY
        service_region = "brazilsouth"
    elif user.subscription.plan == 'subscriber' and own_credentials:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential
        config_dict = json.loads(decrypt_str(credentials.config))

        if credentials.provider_type == 'azure':
            api_key = config_dict.get('apiKey')
            service_region = config_dict.get('region')

            if isinstance(body, SimpleTTSRequest):
                node_tree = Node(
                    type="text",
                    text=body.text,
                    marks=[
                        TTSmarks(
                            type="tts",
                            attrs=TTAttrs(voice=body.voice, inflection=body.inflection)
                        )
                    ]
                )
            else:
                node_tree = body

            segments = parser_nodes(node_tree)
            if with_timeline:
                return await timeline_builder(segments, api_key, service_region)
            else:
                return await ssml_build(segments, api_key, service_region)

        elif credentials.provider_type == 'aws':
            access_api_key = config_dict('accessKeyId')
            secret_access_key = config_dict('secretAccessKey')
            region = config_dict('region')

            if isinstance(body, SimpleTTSRequest):
                node_tree = Node(
                    type="text",
                    text=body.text,
                    marks=[
                        TTSmarks(
                            type="tts",
                            attrs=TTAttrs(voice=body.voice, inflection=body.inflection)
                        )
                    ]
                )
            else:
                node_tree = body

            segments = parser_nodes(node_tree)
            if with_timeline:
                pass
            else:
                return await aws_ssml_build(segments, access_api_key, secret_access_key, region)

    elif user.subscription.plan == 'freemium' and own_credentials:
        credentials = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first().credential
        if credentials.provider_type == 'azure':
            api_key = config_dict.get('apiKey')
            service_region = config_dict.get('region')
        
        elif credentials.provider_type == 'aws':
            access_api_key = config_dict('accessKeyId')
            secret_access_key = config_dict('secretAccessKey')
            region = config_dict('region')
    else:
        raise HTTPException(status_code=403, detail="Process error. Please contact support.")
    


    
