from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()

# class Library(Base):
#     __tablename__ = "libraries"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     name = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     user = relationship("User", back_populates="libraries")
#     books = relationship("Book", back_populates="library")

# class Book(Base):
#     __tablename__ = "books"
#     id = Column(Integer, primary_key=True, index=True)
#     library_id = Column(Integer, ForeignKey("libraries.id"))
#     title = Column(String, nullable=False)
#     pdf_file_path = Column(URLType, nullable=False)
#     text_content = Column(Text)
#     created_at = Column(DateTime, default=datetime.utcnow)

#     library = relationship("Library", back_populates="books")


class AzureCredentials(Base):
    __tablename__ = "azure_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, unique=True, nullable=False)
    azure_key = Column(Text, nullable=False)  # cifrado
    region = Column(String, nullable=False)
    voice = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
