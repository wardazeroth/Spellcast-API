from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    libraries = relationship("Library", back_populates="user")

class Library(Base):
    __tablename__ = "libraries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="libraries")
    books = relationship("Book", back_populates="library")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"))
    title = Column(String, nullable=False)
    pdf_file_path = Column(URLType, nullable=False)
    text_content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    library = relationship("Library", back_populates="books")
