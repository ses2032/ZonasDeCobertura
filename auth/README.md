# Paquete de Autenticación

Este directorio contiene todo el código relacionado con la autenticación OAuth del Sistema de Zonas de Cobertura.

## Estructura del Directorio

```
auth/
├── __init__.py                                    # Paquete Python con exports principales
├── auth.py                                        # Módulo principal de autenticación
├── test_auth.py                                   # Pruebas de autenticación
├── client_secret_*.json                           # Credenciales de Google OAuth
├── CONFIGURACION_AUTENTICACION.md                 # Guía de configuración
├── IMPLEMENTACION_AUTENTICACION_RESUMEN.md        # Resumen de implementación
└── README.md                                      # Este archivo
```

## Funcionalidades

### Autenticación con Google OAuth
- Integración completa con Google OAuth 2.0
- Manejo de tokens y sesiones
- Verificación de usuarios con API externa

### Verificación de Usuarios
- Servicio para verificar usuarios registrados
- Comunicación con API externa
- Manejo de errores y timeouts

### Middleware de Autorización
- Decorador `@login_required` para proteger rutas
- Gestión de sesiones de usuario
- Funciones de utilidad para autenticación

## Uso

### Importación desde el paquete principal

```python
from auth import (
    init_oauth,
    register_auth_routes,
    get_user_verification_service,
    login_required
)
```

### Configuración en la aplicación Flask

```python
from auth import init_oauth, register_auth_routes, get_user_verification_service

# Inicializar OAuth
oauth = init_oauth(app)

# Obtener servicio de verificación
user_verification_service = get_user_verification_service()

# Registrar rutas de autenticación
register_auth_routes(app, oauth, user_verification_service)
```

### Protección de rutas

```python
from auth import login_required

@app.route('/api/protected')
@login_required
def protected_route():
    return jsonify({'message': 'Ruta protegida'})
```

## Configuración

### Variables de Entorno Requeridas

```env
# Google OAuth
GOOGLE_CLIENT_ID=tu-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback

# Sesión
SECRET_KEY=tu-clave-secreta
PERMANENT_SESSION_LIFETIME=3600

# API Externa
EXTERNAL_API_BASE_URL=http://localhost:5064
EXTERNAL_API_TOKEN=tu-token
```

### Archivo de Credenciales

El archivo `client_secret_*.json` debe contener las credenciales de Google OAuth obtenidas desde Google Cloud Console.

## Rutas de Autenticación

- `GET /auth/login` - Iniciar proceso de login con Google
- `GET /auth/callback` - Callback de Google OAuth
- `GET /auth/logout` - Cerrar sesión
- `GET /auth/status` - Estado de autenticación

## Documentación Adicional

- [CONFIGURACION_AUTENTICACION.md](CONFIGURACION_AUTENTICACION.md) - Guía detallada de configuración
- [IMPLEMENTACION_AUTENTICACION_RESUMEN.md](IMPLEMENTACION_AUTENTICACION_RESUMEN.md) - Resumen de implementación

## Pruebas

Ejecutar las pruebas de autenticación:

```bash
python auth/test_auth.py
```

## Seguridad

- Las credenciales de Google OAuth se mantienen en archivos separados
- Uso de sesiones seguras con Flask
- Verificación de usuarios contra API externa
- Manejo seguro de tokens OAuth
