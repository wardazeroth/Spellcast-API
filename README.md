# API Spellcast

Backend para el proyecto Spellcast, construido con Django REST Framework.

## Endpoints

- `GET /`: Devuelve un status 200 y un mensaje de confirmación.
  ```json
  {
      "status": "ok",
      "message": "API Spellcast activa"
  }
  ```

## Documentación interactiva

- **Swagger UI**: [/swagger/](http://127.0.0.1:8000/swagger/)
- **ReDoc**: [/redoc/](http://127.0.0.1:8000/redoc/)

## Requisitos

- Python 3.8+
- Django
- Django REST Framework

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/Spellcast-API.git
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta el servidor:
   ```bash
   python manage.py runserver
   ```