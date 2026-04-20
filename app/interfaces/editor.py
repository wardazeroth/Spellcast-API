from pydantic import BaseModel
from typing import Optional

class TTAttrs(BaseModel):
    characterId : Optional[str]= None
    voice: str = "default"
    inflection: str = "default"

class TTSmarks(BaseModel):
    type: str
    attrs: Optional[TTAttrs]=None

class Node(BaseModel):
    type: str
    text: Optional[str]=None
    marks: Optional[list[TTSmarks]]=None
    content: Optional[list["Node"]]=None

class TTSRequest(BaseModel):
    body: Node
    own_credentials: Optional[bool]=False
