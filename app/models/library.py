from uuid import uuid4
from app.integrations.alchemy import engine, Base
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

class Document(Base):
    __tablename__ = "document"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)   # TODO Buscar solución para pdf's 
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Library(Base):
    __tablename__ = "library"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", uselist=False)

class DocumentLibrary(Base):
    __tablename__ = "documentlibrary"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.document.id"), nullable=True)
    library_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.library.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
 
    document = relationship("Document")
    library = relationship("Library")    

Document.documentlibrary = relationship(
    DocumentLibrary,
    back_populates="document",
    uselist=False
)

Library.documentlibrary = relationship(
    DocumentLibrary,
    back_populates="library",
    uselist=False
)