from pydantic import BaseModel
from typing import Optional, List

class TTAttrs(BaseModel):
    characterId : Optional[str]= None
    characterName: Optional[str] = None
    voice: Optional[str] = "default"
    inflection: Optional[str] = "default"

class TTSmarks(BaseModel):
    type: str
    attrs: Optional[TTAttrs]=None
    
class Node(BaseModel):
    type: str
    text: Optional[str]=None
    content: Optional[List["Node"]]=None
    marks: Optional[List[TTSmarks]]=None

Node.model_rebuild()

class TTSRequest(BaseModel):
    body: Node
    own_credentials: Optional[bool]=False
