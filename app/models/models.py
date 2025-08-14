from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import URLType
from datetime import datetime
from uuid import uuid4
from app.database import engine, Base

# Base = declarative_base()  # unificar todo bajo este Base

# reflejar Users desde schema 'accounts'
class Users(Base):
    __table__ = Table(
        "users",
        Base.metadata,
        autoload_with=engine,
        schema="accounts"
    )

# Tablas nuevas en spellcast
class AzureCredentials(Base):
    __tablename__ = "azure_credentials"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, unique=True, nullable=False)
    azure_key = Column(Text, nullable=False)
    region = Column(String, nullable=False)
    voice = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSubscription(Base):
    __tablename__ = "user_subscription"
    __table_args__ = {"schema": "spellcast"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("accounts.users.id"), unique=True, nullable=False)
    plan = Column(String, nullable=False)

    user = relationship("Users", uselist=False)

#relacion bidireccional, desde Users a UserSubscription
Users.subscription = relationship(
    UserSubscription,
    uselist=False, 
    back_populates="user"
) 
