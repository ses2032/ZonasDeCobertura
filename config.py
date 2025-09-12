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
    # CONFIGURACIÓN DE BASE DE DATOS
    # =====================================================================
    # Ruta completa al archivo de base de datos SQLite
    # os.path.dirname(__file__) obtiene el directorio donde está este archivo
    # os.path.join() une rutas de manera compatible con el sistema operativo
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'zonas_cobertura.db')
    
    # =====================================================================
    # CONFIGURACIÓN DE FLASK
    # =====================================================================
    # Clave secreta para firmar cookies y sesiones
    # os.environ.get() obtiene variables de entorno, con valor por defecto si no existe
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Modo debug: True para desarrollo, False para producción
    # Convierte la variable de entorno a booleano
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
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
    
    # Configuración de base de datos para producción
    # Puede ser una URL de base de datos externa (PostgreSQL, MySQL, etc.)
    DATABASE_URL = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """
    Configuración específica para el entorno de testing.
    
    Esta configuración se usa cuando se ejecutan las pruebas unitarias.
    Incluye configuraciones que facilitan las pruebas y aislamiento.
    """
    # Activar modo testing
    TESTING = True
    
    # Usar base de datos en memoria para las pruebas
    # Esto hace que las pruebas sean más rápidas y aisladas
    DATABASE_PATH = ':memory:'

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
