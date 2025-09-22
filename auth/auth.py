# =============================================================================
# MÓDULO DE AUTENTICACIÓN - GOOGLE OAUTH Y VERIFICACIÓN DE USUARIOS
# =============================================================================
"""
Este módulo contiene toda la lógica de autenticación de la aplicación:
- Autenticación con Google OAuth
- Verificación de usuarios registrados en la API externa
- Gestión de sesiones de usuario
- Middleware de autorización para rutas protegidas
"""

# =============================================================================
# IMPORTS - Importación de librerías necesarias
# =============================================================================

from flask import Flask, request, session, redirect, url_for, jsonify, current_app
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import logging
from typing import Optional, Dict, Any
from config import Config

# Crear un logger específico para este módulo
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN DE OAUTH
# =============================================================================

def init_oauth(app: Flask) -> OAuth:
    """
    Inicializa la configuración de OAuth para la aplicación Flask.
    
    Args:
        app (Flask): Instancia de la aplicación Flask
        
    Returns:
        OAuth: Instancia configurada de OAuth
    """
    logger.info("Inicializando configuración de OAuth")
    
    # Verificar que las credenciales estén configuradas
    client_id = app.config.get('GOOGLE_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.warning("Credenciales de Google OAuth no encontradas en la configuración")
        logger.warning("La aplicación se ejecutará sin autenticación OAuth (modo desarrollo)")
        return None  # Retornar None en lugar de lanzar error
    
    logger.info(f"Credenciales OAuth encontradas - Client ID: {client_id[:20]}...")
    
    oauth = OAuth(app)
    
    # Configurar Google OAuth con configuración manual completa
    google = oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        access_token_url='https://oauth2.googleapis.com/token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri=None,  # Se especificará en cada llamada
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    # Configurar metadata completa para evitar errores
    google._server_metadata = {
        'authorization_endpoint': 'https://accounts.google.com/o/oauth2/auth',
        'token_endpoint': 'https://oauth2.googleapis.com/token',
        'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs',
        'issuer': 'https://accounts.google.com',
        'response_types_supported': ['code'],
        'subject_types_supported': ['public'],
        'id_token_signing_alg_values_supported': ['RS256'],
        'scopes_supported': ['openid', 'email', 'profile']
    }
    
    # Configurar el endpoint de JWKS explícitamente
    google._jwks_uri = 'https://www.googleapis.com/oauth2/v3/certs'
    
    logger.info("Configuración de OAuth completada exitosamente")
    return oauth

# =============================================================================
# CLASE DE VERIFICACIÓN DE USUARIOS
# =============================================================================

class UserVerificationService:
    """
    Servicio para verificar si un usuario está registrado en la API externa.
    
    Este servicio se comunica con la API externa para verificar si un usuario
    con un email específico está registrado y tiene permisos de administrador.
    """
    
    def __init__(self, config: Config):
        """
        Inicializa el servicio de verificación de usuarios.
        
        Args:
            config (Config): Configuración de la aplicación
        """
        self.base_url = config.EXTERNAL_API_BASE_URL
        self.token = config.EXTERNAL_API_TOKEN
        self.timeout = config.EXTERNAL_API_TIMEOUT
        self.endpoint = config.VERIFICAR_USUARIO_ADMIN_ENDPOINT
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def verify_user(self, email: str, additional_headers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Verifica si un usuario está registrado en la API externa.
        
        Args:
            email (str): Email del usuario a verificar
            additional_headers (Optional[Dict]): Headers adicionales (ej: rate limiting)
            
        Returns:
            Dict[str, Any]: Diccionario con información del usuario si está registrado,
                           o None si no está registrado
                           
        Raises:
            requests.RequestException: Si hay un error al comunicarse con la API externa
        """
        try:
            # Construir la URL completa con formato RESTful
            url = f"{self.base_url}{self.endpoint}/{email}"
            
            logger.info(f"Verificando usuario con email: {email}")
            logger.info(f"Llamando a la API: {url}")
            
            # Combinar headers base con headers adicionales (rate limiting, etc.)
            headers = self.headers.copy()
            if additional_headers:
                headers.update(additional_headers)
                logger.info(f"Headers adicionales incluidos: {list(additional_headers.keys())}")
                logger.info(f"Headers adicionales completos: {additional_headers}")
            
            # Logging detallado de headers que se envían a la API externa
            logger.info("=== ENVIANDO PETICIÓN A API EXTERNA ===")
            logger.info(f"URL: {url}")
            logger.info(f"Headers que se envían: {headers}")
            logger.info(f"Email como parte de la URL: {email}")
            
            # Hacer la petición GET a la API externa
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.timeout
            )
            
            logger.info(f"Respuesta de API externa: {response.status_code}")
            logger.info(f"Headers de respuesta: {dict(response.headers)}")
            logger.info("=== FIN PETICIÓN A API EXTERNA ===")
            
                                                
            # Si la respuesta es exitosa (200-299), el usuario está registrado
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Usuario verificado exitosamente: {email}")
                return {
                    'registered': True,
                    'user_data': user_data
                }
            
            # Si la respuesta es 404, el usuario no está registrado
            elif response.status_code == 404:
                logger.info(f"Usuario no registrado: {email}")
                return {
                    'registered': False,
                    'user_data': None
                }
            
            # Otros errores HTTP
            else:
                logger.error(f"Error HTTP {response.status_code} al verificar usuario: {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al verificar usuario: {email}")
            raise requests.RequestException("Timeout al conectar con la API de verificación")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión al verificar usuario: {email}")
            raise requests.RequestException("Error de conexión con la API de verificación")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al verificar usuario {email}: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Error inesperado al verificar usuario {email}: {str(e)}")
            raise requests.RequestException(f"Error inesperado: {str(e)}")

# =============================================================================
# FUNCIONES DE RATE LIMITING
# =============================================================================

def extract_rate_limit_headers(request) -> Dict[str, str]:
    """
    Extrae los headers de rate limiting de la petición entrante.
    
    Esta función busca el header 'x-ratelimit-info' en la petición
    y lo prepara para ser reenviado a la API externa.
    
    Args:
        request: Objeto request de Flask que contiene los headers
        
    Returns:
        dict: Diccionario con headers de rate limiting para reenviar
    """
    rate_limit_headers = {}
    
    # Logging detallado para debugging
            
    # Buscar el header x-ratelimit-info (Flask convierte headers a minúsculas)
    rate_limit_info = request.headers.get('x-ratelimit-info') or request.headers.get('X-Ratelimit-Info')
    
    if rate_limit_info:
        rate_limit_headers['x-ratelimit-info'] = rate_limit_info
        logger.info(f"Header de rate limiting encontrado: {rate_limit_info[:100]}...")
    else:
        logger.info("No se encontró header de rate limiting en la petición")
    
    return rate_limit_headers

# =============================================================================
# FUNCIONES DE AUTENTICACIÓN
# =============================================================================

def login_required(f):
    """
    Decorador para proteger rutas que requieren autenticación.
    
    Este decorador verifica que el usuario tenga una cookie válida
    y esté registrado en la API externa antes de permitir el acceso.
    En modo desarrollo sin OAuth configurado, permite el acceso libre.
    
    Args:
        f: Función a decorar
        
    Returns:
        Función decorada que verifica autenticación
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # En modo desarrollo sin OAuth, permitir acceso libre
        from flask import current_app
        if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
            logger.info("Modo desarrollo sin OAuth - permitiendo acceso libre")
            return f(*args, **kwargs)
        try:
            import json
            import base64
            from datetime import datetime
            # Verificar cookie de autenticación
            auth_cookie = request.cookies.get('auth_user')
            
            if not auth_cookie:
                logger.info("Acceso denegado: no hay cookie de autenticación")
                return jsonify({'error': 'Autenticación requerida'}), 401
            
            # Decodificar cookie
            try:
                cookie_data = json.loads(base64.b64decode(auth_cookie).decode())
            except Exception as e:
                logger.error(f"Error decodificando cookie: {str(e)}")
                return jsonify({'error': 'Cookie de autenticación inválida'}), 401
            
            # Verificar si la cookie ha expirado
            expires_at = datetime.fromisoformat(cookie_data.get('expires_at', ''))
            if datetime.utcnow() > expires_at:
                logger.info("Acceso denegado: cookie expirada")
                return jsonify({'error': 'Sesión expirada'}), 401
            
            # Verificar usuario contra la API externa
            email = cookie_data.get('email')
            if not email:
                logger.info("Acceso denegado: email no encontrado en cookie")
                return jsonify({'error': 'Información de usuario inválida'}), 401
            
            try:
                # Extraer headers de rate limiting de la petición entrante
                rate_limit_headers = extract_rate_limit_headers(request)
                verification_result = user_verification_service.verify_user(email, rate_limit_headers)
                if not verification_result['registered']:
                    logger.info(f"Acceso denegado: usuario no registrado: {email}")
                    return jsonify({'error': 'Usuario no autorizado'}), 403
            except requests.RequestException as e:
                logger.error(f"Error verificando usuario: {str(e)}")
                return jsonify({'error': 'Error de verificación'}), 500
            
            # Usuario autorizado
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error en decorador login_required: {str(e)}")
            return jsonify({'error': 'Error de autenticación'}), 500
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Obtiene la información del usuario actual desde la cookie.
    
    Returns:
        Optional[Dict[str, Any]]: Información del usuario si está autenticado,
                                None en caso contrario
    """
    try:
        import json
        import base64
        from datetime import datetime
        auth_cookie = request.cookies.get('auth_user')
        if not auth_cookie:
            return None
        
        cookie_data = json.loads(base64.b64decode(auth_cookie).decode())
        
        # Verificar si la cookie ha expirado
        expires_at = datetime.fromisoformat(cookie_data.get('expires_at', ''))
        if datetime.utcnow() > expires_at:
            return None
        
        return {
            'email': cookie_data.get('email'),
            'name': cookie_data.get('name'),
            'picture': cookie_data.get('picture')
        }
    except Exception as e:
        logger.error(f"Error obteniendo usuario actual: {str(e)}")
        return None

def is_user_authenticated() -> bool:
    """
    Verifica si el usuario actual está autenticado.
    
    Returns:
        bool: True si el usuario está autenticado, False en caso contrario
    """
    return get_current_user() is not None

def logout_user():
    """
    Cierra la sesión del usuario actual.
    """
    try:
        user = get_current_user()
        if user:
            logger.info(f"Usuario deslogueado: {user.get('email', 'unknown')}")
    except Exception as e:
        logger.error(f"Error al obtener usuario para logout: {str(e)}")
    
    # Limpiar sesión (por compatibilidad)
    session.clear()

# =============================================================================
# RUTAS DE AUTENTICACIÓN
# =============================================================================

def register_auth_routes(app: Flask, oauth: OAuth, user_verification_service: UserVerificationService):
    """
    Registra las rutas de autenticación en la aplicación Flask.
    
    Args:
        app (Flask): Instancia de la aplicación Flask
        oauth (OAuth): Instancia configurada de OAuth
        user_verification_service (UserVerificationService): Servicio de verificación de usuarios
    """
    
    @app.route('/auth/login')
    def login():
        """
        Inicia el proceso de login con Google OAuth.
        
        Redirige al usuario a Google para autenticarse.
        """
        try:
            logger.info("Iniciando proceso de login con Google OAuth")
            
            # Verificar configuración
            client_id = app.config.get('GOOGLE_CLIENT_ID')
            client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
            redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
            
            logger.info(f"Client ID configurado: {client_id[:20] if client_id else 'None'}...")
            logger.info(f"Client Secret configurado: {'Sí' if client_secret else 'No'}")
            logger.info(f"Redirect URI: {redirect_uri}")
            
            if not client_id or not client_secret:
                logger.error("Credenciales de Google OAuth no configuradas")
                return jsonify({'error': 'Configuración de Google OAuth incompleta'}), 500
            
            # Obtener el cliente de Google OAuth
            google = oauth.google
            logger.info("Cliente OAuth obtenido exitosamente")
            
            # Usar la URI de redirección configurada
            logger.info(f"Redirigiendo a Google OAuth con URI: {redirect_uri}")
            return google.authorize_redirect(redirect_uri)
            
        except Exception as e:
            logger.error(f"Error al iniciar login: {str(e)}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            return jsonify({'error': 'Error al iniciar el proceso de login'}), 500
    
    @app.route('/auth/callback')
    def auth_callback():
        """
        Maneja el callback de Google OAuth después de la autenticación.
        
        Crea una cookie de autenticación con el email del usuario.
        """
        try:
            logger.info("Iniciando callback de autenticación")
            logger.info(f"Parámetros recibidos: {dict(request.args)}")
            
            # Obtener el código de autorización directamente de los parámetros
            code = request.args.get('code')
            state = request.args.get('state')
            
            if not code:
                logger.error("No se recibió código de autorización")
                return redirect(url_for('index') + '?error=auth_failed')
            
            logger.info("Intercambiando código de autorización por tokens usando requests")
            import requests
            import json
            
            # Intercambiar código por tokens usando requests directamente
            token_url = 'https://oauth2.googleapis.com/token'
            token_data = {
                'client_id': app.config['GOOGLE_CLIENT_ID'],
                'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': app.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
            }
            
            token_response = requests.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                logger.error(f"Error obteniendo tokens: {token_response.status_code} - {token_response.text}")
                return redirect(url_for('index') + '?error=auth_failed')
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                logger.error("No se pudo obtener access token")
                return redirect(url_for('index') + '?error=auth_failed')
            
            logger.info("Tokens obtenidos exitosamente")
            
            # Obtener información del usuario desde Google
            logger.info("Obteniendo información del usuario desde Google")
            
            user_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if user_response.status_code != 200:
                logger.error(f"Error obteniendo información del usuario: {user_response.status_code}")
                return redirect(url_for('index') + '?error=auth_failed')
            
            user_data = user_response.json()
            logger.info(f"Datos del usuario obtenidos: {user_data}")
            
            email = user_data.get('email')
            if not email:
                logger.error("No se pudo obtener el email del usuario desde Google")
                return redirect(url_for('index') + '?error=auth_failed')
            
            logger.info(f"Usuario autenticado con Google: {email}")
            
            # Crear cookie de autenticación con información del usuario
            from flask import make_response
            response = make_response(redirect(url_for('index')))
            
            # Crear cookie con información del usuario
            import base64
            from datetime import datetime, timedelta
            
            user_cookie_data = {
                'email': email,
                'name': user_data.get('name', ''),
                'picture': user_data.get('picture', ''),
                'authenticated_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            # Codificar datos de la cookie
            cookie_value = base64.b64encode(json.dumps(user_cookie_data).encode()).decode()
            
            # Establecer cookie
            response.set_cookie(
                'auth_user',
                cookie_value,
                max_age=24*60*60,  # 24 horas
                httponly=True,
                secure=False,  # Para desarrollo local
                samesite='Lax'
            )
            
            logger.info(f"Cookie de autenticación creada para usuario: {email}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error en callback de autenticación: {str(e)}")
            logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            return redirect(url_for('index') + '?error=auth_failed')
    
    @app.route('/auth/logout')
    def logout():
        """
        Cierra la sesión del usuario actual y elimina la cookie.
        """
        from flask import make_response
        
        # Limpiar sesión
        logout_user()
        
        # Crear respuesta y eliminar cookie
        response = make_response(jsonify({'message': 'Sesión cerrada exitosamente'}))
        response.set_cookie('auth_user', '', expires=0)
        
        return response
    
    @app.route('/auth/check-cookie')
    def check_cookie():
        """
        Verifica si existe una cookie de autenticación válida.
        
        Returns:
            JSON con información del usuario si la cookie es válida,
            o indicación de que no hay cookie válida
        """
        try:
            import json
            import base64
            from datetime import datetime
            # Obtener cookie de autenticación
            auth_cookie = request.cookies.get('auth_user')
            
            if not auth_cookie:
                logger.info("No se encontró cookie de autenticación")
                return jsonify({'hasValidCookie': False})
            
            # Decodificar cookie
            try:
                cookie_data = json.loads(base64.b64decode(auth_cookie).decode())
            except Exception as e:
                logger.error(f"Error decodificando cookie: {str(e)}")
                return jsonify({'hasValidCookie': False})
            
            # Verificar si la cookie ha expirado
            expires_at = datetime.fromisoformat(cookie_data.get('expires_at', ''))
            if datetime.utcnow() > expires_at:
                logger.info("Cookie de autenticación expirada")
                return jsonify({'hasValidCookie': False})
            
            # Cookie válida
            user_info = {
                'email': cookie_data.get('email'),
                'name': cookie_data.get('name'),
                'picture': cookie_data.get('picture')
            }
            
            logger.info(f"Cookie válida encontrada para usuario: {user_info['email']}")
            return jsonify({
                'hasValidCookie': True,
                'user': user_info
            })
            
        except Exception as e:
            logger.error(f"Error verificando cookie: {str(e)}")
            return jsonify({'hasValidCookie': False})
    
    @app.route('/auth/verify-user', methods=['GET'])
    def verify_user():
        """
        Verifica si un usuario está registrado en la API externa.
        
        Query Parameters:
            email (str): Email del usuario a verificar
        
        Returns:
            JSON con resultado de la verificación
        """
        try:
            email = request.args.get('email')
            
            if not email:
                return jsonify({'error': 'Parámetro email requerido'}), 400
            
            logger.info(f"Verificando usuario: {email}")
            
            # Verificar usuario contra la API externa
            try:
                # Extraer headers de rate limiting de la petición entrante
                rate_limit_headers = extract_rate_limit_headers(request)
                verification_result = user_verification_service.verify_user(email, rate_limit_headers)
                
                if verification_result['registered']:
                    logger.info(f"Usuario verificado exitosamente: {email}")
                    return jsonify({
                        'verified': True,
                        'user_data': verification_result['user_data']
                    })
                else:
                    logger.info(f"Usuario no registrado: {email}")
                    return jsonify({
                        'verified': False,
                        'error': 'Usuario no registrado en el sistema'
                    }), 404
                    
            except requests.RequestException as e:
                logger.error(f"Error conectando con API externa: {str(e)}")
                return jsonify({
                    'verified': False,
                    'error': 'Error de conexión con el sistema de verificación'
                }), 500
                
        except Exception as e:
            logger.error(f"Error verificando usuario: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    

# =============================================================================
# INICIALIZACIÓN DEL SERVICIO
# =============================================================================

# Variable global para almacenar la instancia del servicio de verificación
user_verification_service = None

def get_user_verification_service() -> UserVerificationService:
    """
    Obtiene la instancia única del servicio de verificación de usuarios (patrón Singleton).
    
    Returns:
        UserVerificationService: Instancia única del servicio
    """
    global user_verification_service
    
    if user_verification_service is None:
        from config import config
        user_verification_service = UserVerificationService(config['default'])
    
    return user_verification_service
