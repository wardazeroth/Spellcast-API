from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from fastapi import HTTPException
from uuid import UUID

class AzureConfigSchema(BaseModel):
    apiKey: str
    region: str

class GCPConfigSchema(BaseModel):
    projectId: str
    clientEmail: str
    privateKey: str

class AWSConfigSchema(BaseModel):
    accessKeyId: str
    secretAccessKey: str
    region: str
    #Optional-> for student account
    sessionToken: Optional[str] = None

class CredentialsUpdate(BaseModel):
    provider_type: Optional[Literal['azure', 'gcp', 'aws', 'custom']] = None
    config: Optional[Dict[str, Any]] = None
    voices: Optional[List[Any]] = None
    shared: Optional[bool] = None
    is_active: Optional[bool] = None
    
class CredentialsCreate(BaseModel):
    provider_type: Literal['azure', 'gcp', 'aws', 'custom'] = 'azure'
    config: Dict[str, Any]
    voices: list | None= None
    shared: bool | None= False

class CredentialResponse(BaseModel):
    id: str
    provider_type: str
    voices: List[Any]
    shared: bool
    is_active: bool

    class Config:
        from_attributes = True

class SetCurrentCredential(BaseModel):
    credential_id: UUID | None = None

def validate_provider_config(provider_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    validators = {
        'azure': AzureConfigSchema,
        'gcp': GCPConfigSchema,
        'aws': AWSConfigSchema
    }

    schema_class = validators.get(provider_type)
    if schema_class:
        try:
            #Revisar que vengan los campos exigidos por el esquema
            validated_data = schema_class(**config)
            return validated_data.model_dump()
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Estructura de 'config' inválida para {provider_type}: {str(e)}" 
            )
    return config