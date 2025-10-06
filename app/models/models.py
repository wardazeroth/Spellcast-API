from uuid import uuid4
from app.integrations.alchemy import engine, Base
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# Reflect Users table from accounts schema
class Users(Base):
    __table__ = Table(
        "users",
        Base.metadata,
        autoload_with=engine,
        schema="accounts"
    )

# New models in spellcast schema
class AzureCredentials(Base):
    __tablename__ = "azure_credentials"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, nullable=False)
    azure_key = Column(Text, nullable=False)
    region = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    voices = Column(JSONB, nullable=False, server_default='[]')
    shared = Column(Boolean, default=False)

class UserSubscription(Base):
    __tablename__ = "user_subscription"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id"), unique=True, nullable=False)
    plan = Column(String, nullable=False)
    current_credential = Column(UUID(as_uuid=True), ForeignKey("spellcast.azure_credentials.id"), nullable=True)

    user = relationship("Users", uselist=False)

# Bidirectional relationship from Users to UserSubscription
Users.subscription = relationship(
    UserSubscription,
    uselist=False, 
    back_populates="user"
) 
