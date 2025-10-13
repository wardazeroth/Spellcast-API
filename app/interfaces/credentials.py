from pydantic import BaseModel

class CredentialsUpdate(BaseModel):
    azure_key: str | None= None
    region: str | None= None
    voices: list | None= None
    shared: bool | None= None
    
class CredentialsCreate(BaseModel):
    azure_key: str 
    region: str
    voices: list | None= None
    shared: bool | None= False