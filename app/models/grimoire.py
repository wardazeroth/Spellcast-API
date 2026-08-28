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

# TCORE-104: renamed from Library -- a user's spell collection, "grimorio" in the product's
# own language ("transcribe a spell to your grimoire").
class Grimoire(Base):
    __tablename__ = "grimoire"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", uselist=False)

class SpellGrimoire(Base):
    __tablename__ = "spellgrimoire"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    spell_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.spell.id"), nullable=True)
    grimoire_id = Column(UUID(as_uuid=True), ForeignKey("spellcast.grimoire.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    spell = relationship("Spell")
    grimoire = relationship("Grimoire")

# Note: back_populates below don't actually correspond to any back_populates on the
# `spell`/`grimoire` relationships declared inside SpellGrimoire above (those have none) —
# this mismatch predates the Document->Spell rename (TCORE-78) and is not something this
# rename introduced or attempted to fix.
Spell.spellgrimoire = relationship(
    SpellGrimoire,
    back_populates="spell",
    uselist=False
)

Grimoire.spellgrimoire = relationship(
    SpellGrimoire,
    back_populates="grimoire",
    uselist=False
)
