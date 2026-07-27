# scripts/migrate_credentials.py

import json
from sqlalchemy.orm import Session
from app.integrations.alchemy import SessionLocal
from app.integrations.fernet import encrypt_str, decrypt_str

# Importa tus modelos. Si borraste AzureCredentials de tu código, 
# puedes definir esta clase rápida aquí solo para leer la tabla vieja.
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class OldAzureCredential(Base):
    __tablename__ = 'azure_credentials'
    __table_args__ = {'schema': 'spellcast'}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    azure_key = Column(Text, nullable=False)
    region = Column(String, nullable=False)
    voices = Column(JSONB, default=[])
    shared = Column(Boolean, default=False)
    created_at = Column(DateTime)

class NewCredential(Base):
    __tablename__ = 'credential'
    __table_args__ = {'schema': 'spellcast'}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    config = Column(Text, nullable=False)
    provider_type = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    voices = Column(JSONB, default=[])
    shared = Column(Boolean, default=False)
    created_at = Column(DateTime)


def run_migration():
    db: Session = SessionLocal()
    try:
        # 1. Obtener todas las credenciales antiguas
        old_creds = db.query(OldAzureCredential).all()
        print(f"Encontradas {len(old_creds)} credenciales antiguas en 'spellcast.azure_credentials'.")

        migrated_count = 0
        for old in old_creds:
            # 2. Desencriptar la key vieja (o usarla en texto plano si no estaba encriptada)
            try:
                raw_apiKey = decrypt_str(old.azure_key)
            except Exception:
                raw_apiKey = old.azure_key

            # 3. Armar el diccionario para la nueva estructura
            config_dict = {
                "apiKey": raw_apiKey,
                "region": old.region
            }

            # 4. Convertir a JSON y Encriptar todo el paquete
            encrypted_config = encrypt_str(json.dumps(config_dict))

            # 5. Crear el registro en la nueva tabla 'credential'
            new_cred = NewCredential(
                id=old.id,  # Conservamos el mismo UUID para mantener coherencia
                user_id=old.user_id,
                config=encrypted_config,
                provider_type="azure",
                is_active=True,
                voices=old.voices if old.voices is not None else [],
                shared=old.shared if old.shared is not None else False,
                created_at=old.created_at
            )

            db.add(new_cred)
            migrated_count += 1

        # 6. Confirmar cambios en la BD
        db.commit()
        print(f"¡Migración exitosa! Se copiaron {migrated_count} credenciales a 'spellcast.credential'.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la migración de datos: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()