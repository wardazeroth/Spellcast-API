# SPELLCAST API

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
│       └── document.py
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
- **documents:** Libros asociados a bibliotecas.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Autenticación mediante Token JWT 
Se instala la librería python-jose, que contiene el módulo jwt (Jason Web Token), y JWTError

## Middleware de Validación de Token
Se ha implementado un middleware de autenticación JWT que protege rutas privadas verificando el token enviado por el cliente a través de cookies.

## Funcionamiento
El middleware intercepta las solicitudes a rutas privadas.

Verifica la existencia de una cookie llamada userToken.

Decodifica el JWT usando la clave privada definida en las variables de entorno.

Si el token es válido, se permite el acceso; de lo contrario, se devuelve un error 401 Unauthorized.

## Variables de entorno necesarias
Asegúrate de definir lo siguiente en tu archivo .env:
```
PRIVATE_SECRET="tu_clave_privada_jwt"
```

## Endpoint: /account
Este endpoint permite validar si el token proporcionado por el cliente sigue siendo válido.

## Solicitud
Método: GET

URL: /account

## Autenticación: 
Se requiere una cookie llamada userToken con un JWT válido.

## Cookies requeridas
Nombre	   Tipo	   Descripción
userToken	JWT	   Token de autenticación del usuario

## Respuesta
200 OK: Token válido. Se retorna información básica del usuario decodificada del token.
401 Unauthorized: Token inválido, expirado o ausente.

## Configuración de Desarrollo: CORS y Manejo de Cookies

Al ejecutar la aplicación en un entorno de desarrollo, es posible que encuentres problemas de Cross-Origin Resource Sharing (CORS), especialmente al trabajar con cookies. Esto ocurre típicamente porque los navegadores tratan a `localhost` y `127.0.0.1` como orígenes diferentes, lo que puede impedir que las cookies se envíen correctamente entre tu frontend (ej., ejecutándose en `http://localhost:5173`) y tu backend (ej., ejecutándose en `http://127.0.0.1:8000`).

Para asegurar un comportamiento correcto de CORS y el manejo de cookies en desarrollo, sigue estos pasos:

### 1. Configuración del Backend

El backend está configurado para permitir condicionalmente solicitudes desde `http://localhost:5173` cuando se ejecuta en un entorno de desarrollo. Esto se controla mediante la variable de entorno `APP_ENV`.

-   **`app/main.py`:** El `CORSMiddleware` está configurado para incluir `http://localhost:5173` en su lista `allow_origins` si `APP_ENV` se establece en `development`.

### 2. Ejecución del Servidor de Desarrollo

Para activar la configuración de CORS de desarrollo y asegurar un manejo consistente del origen, debes:

-   **Establecer `APP_ENV` a `development`:** Esta variable de entorno indica al backend que habilite las reglas de CORS específicas para desarrollo.
-   **Ejecutar Uvicorn con `--host localhost`:** Esto asegura que tu backend sea accesible a través del dominio `localhost`, coincidiendo con el origen de tu frontend.

**Comando de Ejemplo:**

```bash
uvicorn app.main:app --reload --host localhost
```

Siguiendo estos pasos, tu entorno de desarrollo debería manejar correctamente CORS y permitir que las cookies se envíen entre tu frontend y tu backend.
