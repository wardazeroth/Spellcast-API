from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.user import Credential, Users, UserSubscription
from app.integrations.redis import get_cache, set_cache
from app.integrations.fernet import encrypt_str, decrypt_str
from app.integrations.alchemy import get_db
from app.interfaces.credentials import CredentialsCreate, CredentialsUpdate, validate_provider_config
from app.services.azure import validate_key, get_voices_list
from app.services.aws import validate_aws_key
from app.utils.mask import mask
from app.misc.consts import AZURE_VALID_REGIONS, AWS_VALID_REGIONS
import json

router = APIRouter(prefix="/user", tags=["User"])

@router.post('/credentials')
async def create_credentials(request: Request, data: CredentialsCreate, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    valid_config = validate_provider_config(data.provider_type, data.config)

    if data.provider_type == 'azure':
        api_key = valid_config["apiKey"]
        region = valid_config["region"]

        if region not in AZURE_VALID_REGIONS:
            raise HTTPException(
                status_code=422, detail="Invalid region. Please provide a valid Azure region.")
        try:
            await validate_key(region, api_key)
        except HTTPException as e:
            print('Error validating Azure key:', e.detail)
            raise HTTPException(
                status_code=422, detail="Invalid Azure key or region. Please provide valid credentials.")

    elif data.provider_type == 'aws':
        access_key_id = valid_config["accessKeyId"]
        secret_access_key = valid_config["secretAccessKey"]
        region = valid_config["region"]

        if region not in AWS_VALID_REGIONS:
            raise HTTPException(
                status_code=422, detail="Invalid region. Please provide a valid AWS region.")
        try:
            await validate_aws_key(access_key_id, secret_access_key, region, sessionToken=None)
        except HTTPException as e:
            print('Error validating key:', e.detail)
            raise HTTPException(status_code= 422, detail="Invalid AWS key or region. Please provide valid credentials.")
    else:
        pass

    json_config_str = json.dumps(valid_config)
    encrypted_config = encrypt_str(json_config_str)

    db.query(Credential).filter(Credential.user_id== user_id).update({'is_active': False})

    new_credentials = Credential(
        user_id=user.id,
        provider_type = data.provider_type,
        config = encrypted_config,
        shared = data.shared
    )

    db.add(new_credentials)
    db.commit()
    db.refresh(new_credentials)
    return {"message": "Credentials created successfully"}



@router.get('/credentials')
async def get_credentials(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    credentials = db.query(Credential).filter(
        Credential.user_id == user_id).all()

    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")

    response = []

    for cred in credentials:
        config_dict = json.loads(decrypt_str(cred.config))
        if cred.provider_type == 'azure':
            raw_key = config_dict.get("apiKey", "")
            config_dict["apiKey"] = mask(raw_key)
        elif cred.provider_type == 'gcp':
            raw_key = config_dict.get("privateKey", "")
            config_dict["privateKey"] = mask(raw_key)
        elif cred.provider_type == 'aws':
            raw_access_key = config_dict.get("accessKeyId")
            config_dict["accessKeyId"] = mask(raw_access_key)
            raw_secret_key = config_dict.get("secretAccessKey", "")
            config_dict["secretAccessKey"] = mask(raw_secret_key)

        response.append({
            "id": cred.id,
            "provider_type": cred.provider_type,
            "config": config_dict,
            "voices": cred.voices,
            "shared": cred.shared
        })

    return response

@router.get('/credentials/{id}')
async def get_credentials(request: Request, reveal: bool = Query(False), db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    id = request.path_params['id']
    credential = db.query(Credential).filter(
        Credential.id == id, Credential.user_id == user_id).first()

    if not credential:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    config_dict = json.loads(decrypt_str(credential.config))

    if not reveal:
        if credential.provider_type == 'azure':
            raw_key = config_dict.get("apiKey", "")
            config_dict["apiKey"] = mask(raw_key)
        elif credential.provider_type == 'gcp':
            raw_key = config_dict.get("privateKey", "")
            config_dict["privateKey"] = mask(raw_key)
        elif credential.provider_type == 'aws':
            raw_key = config_dict.get("secretAccessKey", "")
            config_dict["secretAccessKey"] = mask(raw_key)

    credential = {
        "id": credential.id,
        "provider_type": credential.provider_type,
        "voices": credential.voices,
        "shared": credential.shared
    }
    return credential

@router.patch('/credentials/{id}')
async def update_credentials(request: Request, data: CredentialsUpdate, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    id = request.path_params['id']
    credential = db.query(Credential).filter(
        Credential.id == id, Credential.user_id == user_id).first()

    try:
        if data.config is not None:
            current_config = json.loads(decrypt_str(credential.config))
            current_config.update(data.config)
            #Validar estructura nueva con pydantic
            current_config = validate_provider_config(credential.provider_type, current_config)

            if credential.provider_type == 'azure':
                if current_config.get("region") not in AZURE_VALID_REGIONS:
                    raise HTTPException(
                        status_code=422, detail="Invalid region. Please provide a valid Azure region.")
                await validate_key(current_config["region"], current_config["apiKey"])

            credential.config = encrypt_str(json.dumps(current_config))

        if data.is_active == True:
            db.query(Credential).filter(Credential.user_id== user_id).update({'is_active': False})
            db.expire_all()
            credential.is_active = data.is_active
        
        if data.voices is not None:
            credential.voices = data.voices

        if data.shared is not None:
            credential.shared = data.shared

        db.commit()
        db.refresh(credential)
        
        credentials = db.query(Credential).filter(Credential.user_id == user_id).all()
        response = []

        for cred in credentials:
            config_dict = json.loads(decrypt_str(cred.config))
            if cred.provider_type == 'azure':
                raw_key = config_dict.get("apiKey", "")
                config_dict["apiKey"] = mask(raw_key)
            elif cred.provider_type == 'gcp':
                raw_key = config_dict.get("privateKey", "")
                config_dict["privateKey"] = mask(raw_key)
            elif cred.provider_type == 'aws':
                raw_access_key = config_dict.get("accessKeyId","")
                config_dict["accessKeyId"] = mask(raw_access_key)
                raw_secret_key = config_dict.get("secretAccessKey", "")
                config_dict["secretAccessKey"] = mask(raw_secret_key)

            response.append({
                "id": cred.id,
                "provider_type": cred.provider_type,
                "config": config_dict,
                "voices": cred.voices,
                "shared": cred.shared,
                "is_active": cred.is_active
            })
        return {"message": "Updated successfully", "credentials": response}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        print('Error updating credentials:', str(e))
        raise HTTPException(
            status_code=500, detail="Internal server error while updating credentials")


@router.delete('/credentials/{id}')
async def delete_credentials(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        id = request.path_params['id']
        credential = db.query(Credential).filter(Credential.id == id, Credential.user_id == user_id).first()

        if not credential:
            raise HTTPException(
                status_code=404, detail="Credentials not found")

        db.delete(credential)
        db.commit()
        
        credentials = db.query(Credential).filter(Credential.user_id == user_id).all()
        response = []

        for cred in credentials:
            config_dict = json.loads(decrypt_str(cred.config))
            if cred.provider_type == 'azure':
                raw_key = config_dict.get("apiKey", "")
                config_dict["apiKey"] = mask(raw_key)
            elif cred.provider_type == 'gcp':
                raw_key = config_dict.get("privateKey", "")
                config_dict["privateKey"] = mask(raw_key)
            elif cred.provider_type == 'aws':
                raw_key = config_dict.get("secretAccessKey", "")
                config_dict["secretAccessKey"] = mask(raw_key)
            response.append({
                "id": cred.id,
                "provider_type": cred.provider_type,
                "config": config_dict,
                "voices": cred.voices,
                "shared": cred.shared
            })

        return {"message": "Deleted successfully", "credentials": response}
    except HTTPException as e:
        raise e
    except Exception as e:
        print('Error deleting credential:', str(e))
        raise HTTPException(
            status_code=500, detail="Internal server error while deleting credential")


@router.get('/voices/{credential_id}')
async def get_voices(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    credential_id = request.path_params['credential_id']
    credential = db.query(Credential).filter(
        Credential.id == credential_id, Credential.user_id == user_id).first()

    if not credential:
        raise HTTPException(status_code=404, detail="Credentials not matched")

    config_dict = json.loads(decrypt_str(credential.config))
    if credential.provider_type == 'azure':
        region = config_dict.get("region")
        api_key = config_dict.get("apiKey")
        cache_key = f"voices:azure:{region}"
        cached = get_cache(cache_key)
        if cached:
                return cached
        valid_voices = await get_voices_list(region, api_key)
        set_cache(cache_key, str(valid_voices))
        return valid_voices
    elif credential.provider_type == 'gcp':
        raise HTTPException(status_code=501, detail="GCP voices provider not implemented yet")
    elif credential.provider_type == 'aws':
        raise HTTPException(status_code=501, detail="AWS voices provider not implemented yet")
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider type")

@router.patch('/current_credential')
async def update_current_credential(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    body = await request.json()
    current_credential = body.get('credential_id')

    credential = db.query(Credential).filter(Credential.id ==
        current_credential, Credential.user_id == user_id).first()
    if not credential:
        raise HTTPException(
            status_code=404, detail="Credential not found or does not belong to the user"
        )

    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id).first()
    subscription.current_credential = current_credential

    db.commit()
    db.refresh(subscription)
    return {"message": "Current credential updated", "current_credential": subscription.current_credential}
