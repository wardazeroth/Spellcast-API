from uuid import uuid4
from app.integrations.alchemy import engine, Base
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

class Spell(Base):
    __tablename__ = "spell"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    # `type`/`file_path` are agnostic to what's actually uploaded (see routers/spell.py's
    # presigned-URL flow) -- this table never persists a PDF binary itself, so there is
    # nothing PDF-specific to solve here (TCORE-90: the original PDF, when a user keeps
    # one, lives client-side only, in Spellcast-Client's own IndexedDB store).
    type = Column(String, nullable=False)
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

class SpellLibrary(Base):
    __tablename__ = "spelllibrary"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    spell_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.spell.id"), nullable=True)
    library_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.library.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    spell = relationship("Spell")
    library = relationship("Library")

# Note: back_populates below don't actually correspond to any back_populates on the
# `spell`/`library` relationships declared inside SpellLibrary above (those have none) —
# this mismatch predates the Document->Spell rename (TCORE-78) and is not something this
# rename introduced or attempted to fix.
Spell.spelllibrary = relationship(
    SpellLibrary,
    back_populates="spell",
    uselist=False
)

Library.spelllibrary = relationship(
    SpellLibrary,
    back_populates="library",
    uselist=False
)
