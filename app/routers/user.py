from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import MetaData, Table, Column, Integer, String, select
from sqlalchemy import create_engine
from app.database import SessionLocal
from app.database import DATABASE_URL
from dotenv import load_dotenv
from app.models.models import AzureCredentials, Users
from app.services.voices import get_voice_cache, set_voice_cache
from utils.fernet_utils import encrypt_str, decrypt_str
from pydantic import BaseModel
import httpx

class CredentialsUpdate(BaseModel):
    azure_key: str | None= None
    region: str | None= None
    
class CredentialsCreate(BaseModel):
    azure_key: str 
    region: str 
    
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
        
def mask(secret: str | None, show: int= 3, mask_char:str = '*')-> str:
    return (mask_char * 6) + secret[-show:]

async def validate_key(region: str, azure_key: str) -> bool:
    url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": azure_key,
    'Content-Type': 'application/x-www-form-urlencoded'} 
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail='error fetching key')
        return resp

async def get_voices_list(region, azure_key):
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    headers = {"Ocp-Apim-Subscription-Key": azure_key}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail='error fetching voice in list')
        voices = resp.json()
        return voices
        

VALID_REGIONS = { "eastus","eastus2","westus","westus2","westeurope","northeurope","brazilsouth","southcentralus","uksouth","francecentral","germanywestcentral","swedencentral","switzerlandnorth","uaenorth","australiaeast","japaneast","koreacentral","canadacentral","centralindia","southafricanorth"}

@router.post('/credentials')
async def create_credentials(request: Request, data: CredentialsCreate, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    usuario= db.query(Users).filter(Users.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        await validate_key(data.region, data.azure_key)
        
        encrypt_str_key = encrypt_str(data.azure_key)

        if data.region not in VALID_REGIONS:
            raise HTTPException(status_code=422, detail="Invalid region. Please provide a valid Azure region.")
        
        #Consultar en api de voices por región si la voz es válida para esa region
        # valid_voice =await voices_endpoint(data.region, data.azure_key, data.voice)
        
        # if not valid_voice:
        #     raise HTTPException(status_code=422, detail=f'invalid voice {data.voice} for the region {data.region}')
            
        credentials_exists= db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).first()
        
        new_credentials = AzureCredentials(
            user_id=usuario.id,
            azure_key=encrypt_str_key,
            region=data.region,
        )
        
        db.add(new_credentials) 
        db.commit()
        db.refresh(new_credentials)
        return {"message": "Credentials created successfully"}
                
    except HTTPException as e:
        print('Error validating Azure key:', e.detail)
        raise HTTPException(status_code=422, detail="Invalid Azure key or region. Please provide valid credentials.")

@router.get('/credentials')
async def get_credentials(request: Request, reveal: bool = Query(False), db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    usuario = db.query(Users).filter(Users.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")

    credenciales_list = db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).all()
    
    if not credenciales_list:
        raise HTTPException(status_code=404, detail="Credentials not found")

    response_data = []
    for cred in credenciales_list:
        decrypted_key = decrypt_str(cred.azure_key)
        masked_key = mask(decrypted_key)
        response_data.append({
            "id": cred.id,
            "region": cred.region,
            "azure_key": masked_key
        })
    
    return response_data

@router.get('/credentials/{id}')
async def get_credentials(request: Request, reveal: bool = Query(False), db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    usuario = db.query(Users).filter(Users.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    id = request.path_params['id']
    credencial = db.query(AzureCredentials).filter(AzureCredentials.id == id and AzureCredentials.user_id == user_id).first()
    
    print('es la cred: ', credencial.id)
    
    if not credencial:
        raise HTTPException(status_code=404, detail="Credentials not found")

    azure_key = credencial.azure_key
    azure_api_key = decrypt_str(azure_key)
    azure_key= mask(azure_api_key)
    
    credencial = {
        'azure_key': azure_api_key if reveal else azure_key,
        'region': credencial.region
    }
    return credencial

@router.patch('/credentials')
async def update_credentials(request: Request, data: CredentialsUpdate, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    usuario= db.query(Users).filter(Users.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    credenciales = db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).first()
    
    if data.azure_key is not None:
        encrypt_str_key = encrypt_str(data.azure_key)
        credenciales.azure_key = encrypt_str_key
        
    if data.region is not None:
        if data.region not in VALID_REGIONS:
            raise HTTPException(status_code=422, detail="Invalid region. Please provide a valid Azure region.")
        credenciales.region = data.region   

    db.commit()
    db.refresh(credenciales)

    return {"message": "Credenciales actualizadas", "credentials": data.dict(exclude_unset=True)}

@router.patch('/credentials/{id}')
async def update_credentials(request: Request, data: CredentialsUpdate, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    usuario= db.query(Users).filter(Users.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        await validate_key(data.region, data.azure_key)
        id = request.path_params['id']  
        credencial = db.query(AzureCredentials).filter(AzureCredentials.id == id and AzureCredentials.user_id == user_id).first()
        
        if data.azure_key is not None:
            encrypt_str_key = encrypt_str(data.azure_key)
            credencial.azure_key = encrypt_str_key
            
        if data.region is not None:
            if data.region not in VALID_REGIONS:
                raise HTTPException(status_code=422, detail="Invalid region. Please provide a valid Azure region.")
            credencial.region = data.region   

        db.commit()
        db.refresh(credencial)

        return {"message": "Credenciales actualizadas", "credential_id": credencial.id}
    except HTTPException as e:
        print('Error validating Azure key:', e.detail)
        raise HTTPException(status_code=422, detail="Invalid Azure key or region. Please provide valid credentials.")

@router.delete('/credentials')
async def update_credentials(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    usuario= db.query(Users).filter(Users.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    credenciales = db.query(AzureCredentials).filter(AzureCredentials.user_id == user_id).first()
    
    if not credenciales:
        raise HTTPException(status_code=404, detail="Credentials not found")
    
    db.delete(credenciales)
    db.commit()

    return {"message": "Credenciales eliminadas correctamente"}
    
@router.delete('/credentials/{id}')
async def update_credentials(request: Request, db: Session = Depends(get_db)): 
    user_id = request.state.user.get('id')
    usuario= db.query(Users).filter(Users.id == user_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    try:     
        id = request.path_params['id']  
        credencial = db.query(AzureCredentials).filter(AzureCredentials.id == id and AzureCredentials.user_id == user_id).first()
        
        if not credencial:
            raise HTTPException(status_code=404, detail="Credentials not found")
        
        db.delete(credencial)
        db.commit()

        return {"message": "Credencial eliminada correctamente"} 
    except HTTPException as e:
        print('Error deleting credential:', e.detail)
        raise HTTPException(status_code=422, detail="Error deleting credential. Please try again.")

@router.get('/voices/{credential_id}')

async def get_voices(request: Request, db: Session = Depends(get_db)):
    user_id = request.state.user.get('id')
    usuario = db.query(Users).filter(Users.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")
    
    credential_id = request.path_params['credential_id']
    credential = db.query(AzureCredentials).filter(AzureCredentials.id == credential_id and AzureCredentials.user_id == user_id).first()
    
    #Recordar: Dejar de comentar
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credentials not matched")

    azure_key = credential.azure_key
    azure_api_key = decrypt_str(azure_key)
    
    cached = get_voice_cache(credential.region)
    if cached:
        print('Hay caché!!')
        return cached  
    
    valid_voices = await get_voices_list(credential.region, azure_api_key)
    set_voice_cache(credential.region, str(valid_voices))
    print('nuevo caché!') 
    
    return valid_voices