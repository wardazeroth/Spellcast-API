# PROYECTO_SPELLCAST

Spellcast es una API desarrollada con FastAPI y SQLAlchemy para la gestión de usuarios, bibliotecas y libros, permitiendo almacenar archivos PDF y extraer su contenido de texto.

## Características

- **Usuarios:** Registro y gestión de usuarios.
- **Bibliotecas:** Cada usuario puede tener múltiples bibliotecas.
- **Libros:** Cada biblioteca puede contener múltiples libros, con almacenamiento de la ruta del PDF y su texto extraído.
- **Migraciones:** Gestión de migraciones de base de datos con Alembic.
- **Variables de entorno:** Configuración segura mediante `.env`.

## Estructura del proyecto

```
PROYECTO_SPELLCAST/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── seed.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   └── routers/
│       ├── __init__.py
│       ├── user.py
│       ├── library.py
│       └── book.py
│
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       └── bc75384515ca_initial_tables.py
│
├── .env.example
├── alembic.ini
├── LICENSE
├── README.MD
├── requirements.txt
```

## Instalación

1. **Clona el repositorio**
   ```sh
   git clone <url-del-repositorio>
   cd PROYECTO_SPELLCAST
   ```

2. **Crea y activa un entorno virtual**
   ```sh
   python -m venv venv
   # En Linux/Mac:
   source venv/bin/activate
   # En Windows:
   venv\Scripts\activate
   ```

3. **Instala las dependencias**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configura las variables de entorno**
   - Copia `.env.example` a `.env` y edítalo con tu cadena de conexión a PostgreSQL.

5. **Ejecuta las migraciones**
   ```sh
   alembic upgrade head
   ```

6. **(Opcional) Inserta datos de prueba**
   ```sh
   python app/seed.py
   ```

7. **Inicia el servidor**
   ```sh
   uvicorn app.main:app --reload
   ```

## Uso

Accede a la documentación interactiva de la API en:  
[http://localhost:8000/docs](http://localhost:8000/docs)

## Estructura de la base de datos

- **users:** Usuarios registrados.
- **libraries:** Bibliotecas asociadas a usuarios.
- **books:** Libros asociados a bibliotecas.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.