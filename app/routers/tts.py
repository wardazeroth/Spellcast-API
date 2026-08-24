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
import json

router = APIRouter(prefix="/tts", tags=["tts"])


def body_type_request(body, provider):
    """Normalize either request shape into a single-node Node tree so parser_nodes() always
    has one contract to walk. SimpleTTSRequest has no marks of its own, so its voice/inflection
    become the synthetic text node's single 'tts' mark — falling back to the provider's default
    voice (resolved here, not client-side) when the caller didn't request one. Wrapped in a
    paragraph, not a bare text node: parser_nodes() only splits sentences at the
    paragraph/heading level (see app/utils/parser.py), so a root-level text node would never
    be walked at all."""
    if isinstance(body, SimpleTTSRequest):
        selected_voice = body.voice if body.voice is not None else DEFAULT_VOICES.get(provider)
        return Node(
            type="paragraph",
            content=[
                Node(
                    type="text",
                    text=body.text,
                    marks=[
                        TTSmarks(
                            type="tts",
                            attrs=TTAttrs(voice=selected_voice, inflection=body.inflection)
                        )
                    ]
                )
            ]
        )
    return body


@router.post('/')
async def text_to_speech(body: Union[Node, SimpleTTSRequest], own_credentials: bool = True, with_timeline: bool = False, db: Session = Depends(get_db), request: Request = None):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Subscriber without own credentials → platform Azure key.
    if user.subscription.plan == 'subscriber' and not own_credentials:
        config_dict = {'apiKey': AZURE_API_KEY, 'region': "brazilsouth"}
        return await azure_synthesis(config_dict, body, with_timeline)

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
            return await azure_synthesis(config_dict, body, with_timeline)
        elif provider == 'aws':
            return await aws_synthesis(config_dict, body, with_timeline)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    raise HTTPException(status_code=403, detail="Process error. Please contact support.")


async def azure_synthesis(config_dict, body, with_timeline):
    api_key = config_dict.get('apiKey')
    service_region = config_dict.get('region')

    node_tree = body_type_request(body, 'azure')
    segments = parser_nodes(node_tree, 'azure')

    if with_timeline:
        return await azure_time_builder(segments, api_key, service_region)
    return await azure_ssml_build(segments, api_key, service_region)


async def aws_synthesis(config_dict, body, with_timeline):
    access_api_key = config_dict.get('accessKeyId')
    secret_access_key = config_dict.get('secretAccessKey')
    region = config_dict.get('region')

    node_tree = body_type_request(body, 'aws')
    segments = parser_nodes(node_tree, 'aws')
    voice_id = segments[0]['voice'] if segments else None

    if with_timeline:
        return await aws_timeline_builder(segments, voice_id, access_api_key, secret_access_key, region)
    return await aws_ssml_build(voice_id, segments, access_api_key, secret_access_key, region)
