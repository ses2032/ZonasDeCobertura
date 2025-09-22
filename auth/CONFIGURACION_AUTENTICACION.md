# Configuración de Autenticación con Google OAuth

Este documento explica cómo configurar la autenticación con Google OAuth para el Sistema de Zonas de Cobertura.

## Requisitos Previos

1. **Cuenta de Google**: Necesitas una cuenta de Google para crear las credenciales OAuth.
2. **Google Cloud Console**: Acceso a [Google Cloud Console](https://console.cloud.google.com/).

## Paso 1: Crear un Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Anota el **Project ID** del proyecto

## Paso 2: Habilitar la API de Google+

1. En el menú lateral, ve a **APIs & Services** > **Library**
2. Busca "Google+ API" y habilítala
3. También habilita "Google OAuth2 API" si está disponible

## Paso 3: Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services** > **Credentials**
2. Haz clic en **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Si es la primera vez, configura la pantalla de consentimiento OAuth:
   - Selecciona **External** para usuarios externos
   - Completa la información requerida (nombre de la app, email de soporte, etc.)
4. Selecciona **Web application** como tipo de aplicación
5. Configura las URLs autorizadas:
   - **Authorized JavaScript origins**: `http://localhost:5000`
   - **Authorized redirect URIs**: `http://localhost:5000/auth/callback`
6. Haz clic en **Create**

## Paso 4: Obtener las Credenciales

Después de crear las credenciales, obtendrás:
- **Client ID**: Algo como `123456789-abcdefg.apps.googleusercontent.com`
- **Client Secret**: Una cadena secreta

## Paso 5: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Configuración de Flask
SECRET_KEY=tu-clave-secreta-super-segura-aqui
FLASK_DEBUG=True

# Configuración de Google OAuth
GOOGLE_CLIENT_ID=tu-google-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback

# Configuración de API Externa
EXTERNAL_API_BASE_URL=http://localhost:5064
EXTERNAL_API_TOKEN=070CE54A-CF38-4328-90AC-584A1FB3549F
EXTERNAL_API_TIMEOUT=30

# Configuración de Sesión
PERMANENT_SESSION_LIFETIME=3600
```

## Paso 6: Configurar la API Externa

Asegúrate de que la API externa tenga configurado el endpoint `/internalapi/VerificarUsuarioAdmin` que:

1. **Recibe**: Un JSON con el campo `email`
2. **Retorna**: 
   - **200**: JSON con datos del usuario si está registrado
   - **404**: Error si el usuario no está registrado

Ejemplo de petición:
```json
{
  "email": "usuario@ejemplo.com"
}
```

Ejemplo de respuesta exitosa (200):
```json
{
  "id": 123,
  "nombre": "Juan Pérez",
  "email": "usuario@ejemplo.com",
  "rol": "admin"
}
```

## Paso 7: Instalar Dependencias

```bash
pip install -r requirements.txt
```

## Paso 8: Ejecutar la Aplicación

```bash
python app.py
```

## Configuración para Producción

Para producción, necesitas:

1. **Actualizar las URLs autorizadas** en Google Cloud Console:
   - **Authorized JavaScript origins**: `https://tu-dominio.com`
   - **Authorized redirect URIs**: `https://tu-dominio.com/auth/callback`

2. **Configurar variables de entorno** en tu servidor:
   ```env
   SECRET_KEY=clave-super-secreta-para-produccion
   FLASK_DEBUG=False
   GOOGLE_CLIENT_ID=tu-client-id-de-produccion
   GOOGLE_CLIENT_SECRET=tu-client-secret-de-produccion
   GOOGLE_REDIRECT_URI=https://tu-dominio.com/auth/callback
   EXTERNAL_API_BASE_URL=https://tu-api-externa.com
   EXTERNAL_API_TOKEN=tu-token-de-produccion
   ```

3. **Configurar HTTPS**: Google OAuth requiere HTTPS en producción

## Flujo de Autenticación

1. **Usuario hace clic en "Iniciar Sesión"**
2. **Redirige a Google** para autenticación
3. **Usuario se autentica** con Google
4. **Google redirige** de vuelta a `/auth/callback`
5. **Sistema verifica** el usuario con la API externa usando el email
6. **Si está registrado**: Se crea la sesión y se permite el acceso
7. **Si no está registrado**: Se muestra error de acceso denegado

## Troubleshooting

### Error: "redirect_uri_mismatch"
- Verifica que las URLs en Google Cloud Console coincidan exactamente con las de tu aplicación

### Error: "invalid_client"
- Verifica que el Client ID y Client Secret sean correctos

### Error: "Usuario no autorizado"
- Verifica que el endpoint `/internalapi/VerificarUsuarioAdmin` esté funcionando
- Verifica que el usuario esté registrado en la API externa

### Error: "Sesión expirada"
- Verifica que `PERMANENT_SESSION_LIFETIME` esté configurado correctamente
- Verifica que `SECRET_KEY` sea consistente

## Seguridad

- **Nunca** commitees el archivo `.env` al repositorio
- Usa **SECRET_KEY** fuertes y únicos para cada entorno
- Configura **HTTPS** en producción
- Mantén las credenciales de Google OAuth seguras
- Revisa regularmente los permisos en Google Cloud Console
