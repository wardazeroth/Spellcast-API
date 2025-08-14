#Insertar datos ficticios en la base de datos
from sqlalchemy.orm import Session
from app.database import SessionLocal
# from app.models.models import User, Library, Book
from app.models.models import Users, UserSubscription


db: Session = SessionLocal()

# user = User(username="testuser", email="test@example.com")
# db.add(user)
# db.commit()
# db.refresh(user)

# library = Library(name="Main Library", user_id=user.id)
# db.add(library)
# db.commit()
# db.refresh(library)

# book = Book(title="Sample Book", pdf_file_path="http://example.com/sample.pdf", library_id=library.id, text_content="Texto de ejemplo")
# db.add(book)
# db.commit()

subscription = UserSubscription(user_id='e0fb632c-c9f2-40f9-9644-5844d73f5a83', plan="premium")
db.add(subscription)
db.commit()
# db.close()
print("Datos ficticios insertados.")
