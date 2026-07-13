from pydantic import BaseModel
from typing import Optional, List

class TTAttrs(BaseModel):
    characterId: Optional[str] = None
    characterName: Optional[str] = None
    voice: Optional[str] = "default"
    inflection: Optional[str] = "default"

class TTSmarks(BaseModel):
    type: str
    attrs: Optional[TTAttrs] = None

class Node(BaseModel):
    type: str
    text: Optional[str] = None
    marks: Optional[List[TTSmarks]] = None
    content: Optional[List["Node"]] = None

Node.model_rebuild()

class TTSRequest(BaseModel):
    body: Node
    own_credentials: Optional[bool]=False

class Segment(BaseModel):
    text: str
    voice: str
    inflection: str
