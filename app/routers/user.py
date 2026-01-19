from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.user import AzureCredentials, Users, UserSubscription
from app.integrations.redis import get_cache, set_cache
from app.integrations.fernet import encrypt_str, decrypt_str
from app.integrations.alchemy import get_db
from app.interfaces.credentials import CredentialsCreate, CredentialsUpdate
from app.services.azure import validate_key, get_voices_list
from app.utils.mask import mask
from app.misc.consts import VALID_REGIONS

router = APIRouter(prefix="/user", tags=["User"])

@router.post('/credentials')
async def create_credentials(request: Request, data: CredentialsCreate, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await validate_key(data.region, data.azure_key)

        encrypt_str_key = encrypt_str(data.azure_key)

        if data.region not in VALID_REGIONS:
            raise HTTPException(
                status_code=422, detail="Invalid region. Please provide a valid Azure region.")

        new_credentials = AzureCredentials(
            user_id=user.id,
            azure_key=encrypt_str_key,
            region=data.region,
        )

        db.add(new_credentials)
        db.commit()
        db.refresh(new_credentials)
        return {"message": "Credentials created successfully"}

    except HTTPException as e:
        print('Error validating Azure key:', e.detail)
        raise HTTPException(
            status_code=422, detail="Invalid Azure key or region. Please provide valid credentials.")


@router.get('/credentials')
async def get_credentials(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    credentials = db.query(AzureCredentials).filter(
        AzureCredentials.user_id == user_id).all()

    if not credentials:
        raise HTTPException(status_code=404, detail="Credentials not found")

    response = []

    for cred in credentials:
        decrypted_key = decrypt_str(cred.azure_key)
        masked_key = mask(decrypted_key)
        response.append({
            "id": cred.id,
            "region": cred.region,
            "azure_key": masked_key,
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
    credential = db.query(AzureCredentials).filter(
        AzureCredentials.id == id and AzureCredentials.user_id == user_id).first()

    if not credential:
        raise HTTPException(status_code=404, detail="Credentials not found")

    azure_key = credential.azure_key
    azure_api_key = decrypt_str(azure_key)
    azure_key = mask(azure_api_key)

    credential = {
        'azure_key': azure_api_key if reveal else azure_key,
        'region': credential.region
    }
    return credential


@router.patch('/credentials/{id}')
async def update_credentials(request: Request, data: CredentialsUpdate, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if data.region and data.azure_key:
            await validate_key(data.region, data.azure_key)

        id = request.path_params['id']
        credential = db.query(AzureCredentials).filter(
            AzureCredentials.id == id and AzureCredentials.user_id == user_id).first()

        if data.azure_key is not None:
            encrypt_str_key = encrypt_str(data.azure_key)
            credential.azure_key = encrypt_str_key

        if data.region is not None:
            if data.region not in VALID_REGIONS:
                raise HTTPException(
                    status_code=422, detail="Invalid region. Please provide a valid Azure region.")
            credential.region = data.region

        if data.voices is not None:
            credential.voices = data.voices

        if data.shared is not None:
            credential.shared = data.shared

        db.commit()
        db.refresh(credential)
        
        credentials = db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).all()
        response = []

        for cred in credentials:
            decrypted_key = decrypt_str(cred.azure_key)
            masked_key = mask(decrypted_key)
            response.append({
                "id": cred.id,
                "region": cred.region,
                "azure_key": masked_key,
                "voices": cred.voices,
                "shared": cred.shared
            })

        return {"message": "Updated successfully", "credentials": response}
    except HTTPException as e:
        print('Error validating Azure key:', e.detail)
        raise HTTPException(
            status_code=422, detail="Invalid Azure key or region. Please provide valid credentials.")


@router.delete('/credentials/{id}')
async def update_credentials(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        id = request.path_params['id']
        credential = db.query(AzureCredentials).filter(AzureCredentials.id == id and AzureCredentials.user_id == user_id).first()

        if not credential:
            raise HTTPException(
                status_code=404, detail="Credentials not found")

        db.delete(credential)
        db.commit()
        
        credentials = db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).all()
        response = []

        for cred in credentials:
            decrypted_key = decrypt_str(cred.azure_key)
            masked_key = mask(decrypted_key)
            response.append({
                "id": cred.id,
                "region": cred.region,
                "azure_key": masked_key,
                "voices": cred.voices,
                "shared": cred.shared
            })

        return {"message": "Deleted successfully", "credentials": response}
    except HTTPException as e:
        print('Error deleting credential:', e.detail)
        raise HTTPException(
            status_code=422, detail="Error deleting credential. Please try again.")


@router.get('/voices/{credential_id}')
async def get_voices(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    credential_id = request.path_params['credential_id']
    credential = db.query(AzureCredentials).filter(
        AzureCredentials.id == credential_id and AzureCredentials.user_id == user_id).first()

    if not credential:
        raise HTTPException(status_code=404, detail="Credentials not matched")

    azure_key = credential.azure_key
    azure_api_key = decrypt_str(azure_key)
    key = f"voices:{credential.region}"
    cached = get_cache(key)
    if cached:
        return cached

    valid_voices = await get_voices_list(credential.region, azure_api_key)
    key = f"voices:{credential.region}"
    set_cache(key, str(valid_voices))
    return valid_voices


@router.patch('/current_credential')
async def update_current_credential(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    user = db.query(Users).filter(Users.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    body = await request.json()
    current_credential = body.get('credential_id')

    try:
        db.query(AzureCredentials).filter(AzureCredentials.id ==
                                          current_credential and AzureCredentials.user_id == user_id).first()

    except:
        raise HTTPException(
            status_code=404, detail="Credential not found or does not belong to the user")

    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id).first()
    subscription.current_credential = current_credential

    db.commit()
    db.refresh(subscription)
    return {"message": "Current credential updated", "current_credential": subscription.current_credential}
