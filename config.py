# =============================================================================
# CONFIGURACIÓN DEL SISTEMA DE ZONAS DE COBERTURA
# =============================================================================
"""
Este módulo contiene todas las configuraciones de la aplicación, incluyendo
configuraciones para diferentes entornos (desarrollo, producción, testing).

Las configuraciones se organizan en clases que heredan de una clase base Config,
permitiendo tener diferentes configuraciones según el entorno de ejecución.
"""

# =============================================================================
# IMPORTS - Importación de librerías necesarias
# =============================================================================

# os: Para operaciones del sistema operativo y variables de entorno
import os

# =============================================================================
# CLASE BASE DE CONFIGURACIÓN
# =============================================================================

class Config:
    """
    Configuración base de la aplicación.
    
    Esta clase contiene todas las configuraciones por defecto que se aplican
    a todos los entornos. Las clases específicas de entorno pueden sobrescribir
    estos valores según sea necesario.
    """
    
    
    # =====================================================================
    # CONFIGURACIÓN DE FLASK
    # =====================================================================
    # Clave secreta para firmar cookies y sesiones
    # os.environ.get() obtiene variables de entorno, con valor por defecto si no existe
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Modo debug: True para desarrollo, False para producción
    # Convierte la variable de entorno a booleano
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuración del servidor para generar URLs externas
    SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost:5000')
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    
    # =====================================================================
    # CONFIGURACIÓN DE GEOCODIFICACIÓN
    # =====================================================================
    # Servicio de geocodificación a usar ('nominatim', 'google', 'here')
    GEOCODING_SERVICE = 'nominatim'  # Nominatim es gratuito y no requiere API key
    
    # User agent para identificar nuestra aplicación en las peticiones a Nominatim
    NOMINATIM_USER_AGENT = 'zonas_cobertura_app'
    
    # Tiempo límite en segundos para peticiones de geocodificación
    NOMINATIM_TIMEOUT = 10
    
    # =====================================================================
    # CONFIGURACIÓN DE MAPAS
    # =====================================================================
    # Configuración por defecto del mapa (centro y zoom inicial)
    DEFAULT_MAP_CENTER = {
        'lat': -34.6037,  # Latitud de Buenos Aires, Argentina
        'lng': -58.3816,  # Longitud de Buenos Aires, Argentina
        'zoom': 12        # Nivel de zoom inicial (1=planeta, 20=edificio)
    }
    
    # =====================================================================
    # CONFIGURACIÓN DE LÍMITES
    # =====================================================================
    # Número máximo de puntos que puede tener un polígono de zona
    MAX_POLYGON_POINTS = 100
    
    # Número máximo de zonas de cobertura por sucursal
    MAX_ZONES_PER_BRANCH = 10
    
    # =====================================================================
    # CONFIGURACIÓN DE ARCHIVOS
    # =====================================================================
    # Carpeta donde se guardarán archivos subidos por usuarios
    UPLOAD_FOLDER = 'uploads'
    
    # Tamaño máximo de archivo en bytes (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # =====================================================================
    # CONFIGURACIÓN DE LOGGING
    # =====================================================================
    # Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    LOG_LEVEL = 'INFO'
    
    # Archivo donde se guardarán los logs
    LOG_FILE = 'app.log'
    
    # =====================================================================
    # CONFIGURACIÓN DE API EXTERNA
    # =====================================================================
    # URL base de la API externa de sucursales
    EXTERNAL_API_BASE_URL = os.environ.get('EXTERNAL_API_BASE_URL', 'http://localhost:5064')
    
    # Token de autenticación para la API externa
    EXTERNAL_API_TOKEN = os.environ.get('EXTERNAL_API_TOKEN', '070CE54A-CF38-4328-90AC-584A1FB3549F')
    
    # Tiempo límite en segundos para peticiones a la API externa
    EXTERNAL_API_TIMEOUT = int(os.environ.get('EXTERNAL_API_TIMEOUT', '30'))
    
    # =====================================================================
    # CONFIGURACIÓN DE AUTENTICACIÓN GOOGLE OAUTH
    # =====================================================================
    # Credenciales de Google OAuth (obtener desde Google Cloud Console)
    # Primero intentar desde variables de entorno, luego desde archivo JSON
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Si no están en variables de entorno, cargar desde archivo JSON
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        try:
            import json
            credentials_file = os.path.join(os.path.dirname(__file__), 'auth', 'client_secret_292447687984-7ig33t4uv3j738g0mrkeg6tbm6hps8ds.apps.googleusercontent.com.json')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r') as f:
                    credentials = json.load(f)
                    GOOGLE_CLIENT_ID = credentials['web']['client_id']
                    GOOGLE_CLIENT_SECRET = credentials['web']['client_secret']
        except Exception as e:
            print(f"Error cargando credenciales de Google OAuth: {e}")
    
    # URL de redirección después del login (debe estar registrada en Google Console)
    # Para desarrollo, usar la URI que está registrada en Google Console
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', '3600'))  # 1 hora por defecto
    
    # =====================================================================
    # ENDPOINTS DE LA API EXTERNA
    # =====================================================================
    # Endpoint para obtener la lista de sucursales
    SUBSIDIARY_LIST_ENDPOINT = '/internalapi/SubsidiaryList/1'
    
    # Endpoint base para zonas de cobertura (se le agrega el ID de sucursal)
    ZONAS_COBERTURA_ENDPOINT = '/internalapi/GetZonasCobertura'
    
    # Endpoint para guardar nuevas zonas de cobertura
    GUARDAR_ZONA_ENDPOINT = '/internalapi/GuardarZonaCobertura'
    
    # Endpoint para eliminar zonas de cobertura
    ELIMINAR_ZONA_ENDPOINT = '/internalapi/EliminarZonaCobertura'
    
    # Endpoint para verificar usuarios administradores
    VERIFICAR_USUARIO_ADMIN_ENDPOINT = '/internalapi/VerificarUsuarioAdmin'

# =============================================================================
# CONFIGURACIONES ESPECÍFICAS POR ENTORNO
# =============================================================================

class DevelopmentConfig(Config):
    """
    Configuración específica para el entorno de desarrollo.
    
    Esta configuración se usa cuando la aplicación se ejecuta en modo desarrollo.
    Incluye configuraciones que facilitan el desarrollo y debugging.
    """
    # Activar modo debug para desarrollo (recarga automática, mensajes detallados)
    DEBUG = True
    
    # No estamos en modo testing
    TESTING = False

class ProductionConfig(Config):
    """
    Configuración específica para el entorno de producción.
    
    Esta configuración se usa cuando la aplicación se ejecuta en producción.
    Incluye configuraciones de seguridad y rendimiento optimizadas.
    """
    # Desactivar modo debug en producción por seguridad
    DEBUG = False
    
    # No estamos en modo testing
    TESTING = False
    
    # =====================================================================
    # CONFIGURACIONES DE SEGURIDAD PARA PRODUCCIÓN
    # =====================================================================
    # En producción, la SECRET_KEY DEBE venir de variables de entorno
    # Nunca usar claves hardcodeadas en producción
    SECRET_KEY = os.environ.get('SECRET_KEY')
    

class TestingConfig(Config):
    """
    Configuración específica para el entorno de testing.
    
    Esta configuración se usa cuando se ejecutan las pruebas unitarias.
    Incluye configuraciones que facilitan las pruebas y aislamiento.
    """
    # Activar modo testing
    TESTING = True
    

# =============================================================================
# DICCIONARIO DE CONFIGURACIONES
# =============================================================================

# Diccionario que mapea nombres de entorno a clases de configuración
# Esto permite cambiar fácilmente la configuración según el entorno
config = {
    'development': DevelopmentConfig,  # Configuración para desarrollo
    'production': ProductionConfig,    # Configuración para producción
    'testing': TestingConfig,          # Configuración para testing
    'default': DevelopmentConfig       # Configuración por defecto (desarrollo)
}
