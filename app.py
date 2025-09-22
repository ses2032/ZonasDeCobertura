# =============================================================================
# IMPORTS - Importación de librerías y módulos necesarios
# =============================================================================

# Flask: Framework web para crear aplicaciones web en Python
from flask import Flask, request, jsonify, render_template
# CORS: Permite que el navegador haga peticiones desde diferentes dominios
from flask_cors import CORS
# json: Para manejar datos en formato JSON (JavaScript Object Notation)
import json
# requests: Para hacer peticiones HTTP a APIs externas
import requests
# geopy: Librería para geocodificación (convertir direcciones a coordenadas)
from geopy.geocoders import Nominatim
# shapely: Librería para operaciones geométricas (puntos, polígonos, etc.)
from shapely.geometry import Point, Polygon
# os: Para operaciones del sistema operativo
import os
# logging: Para registrar mensajes de log (errores, información, etc.)
import logging
# Importamos nuestro servicio personalizado para la API externa
from api_service import get_api_service
# Importamos la configuración de la aplicación
from config import config
# Importamos el paquete de autenticación
from auth import init_oauth, register_auth_routes, get_user_verification_service, login_required

# =============================================================================
# CONFIGURACIÓN INICIAL DE LA APLICACIÓN FLASK
# =============================================================================

# Crear la instancia de la aplicación Flask
# __name__ es una variable especial de Python que contiene el nombre del módulo actual
app = Flask(__name__)

# Configurar la aplicación con la configuración por defecto
app.config.from_object(config['default'])

# Configuración adicional para sesiones
app.config['SESSION_COOKIE_SECURE'] = False  # Para desarrollo local
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Habilitar CORS (Cross-Origin Resource Sharing) para permitir peticiones desde el frontend
# Esto es necesario cuando el frontend y backend están en diferentes puertos/dominios
# Configurar CORS para permitir cookies de sesión
CORS(app, supports_credentials=True)

# =============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN
# =============================================================================

# Inicializar OAuth para autenticación con Google (opcional en desarrollo)
oauth = init_oauth(app)

# Obtener el servicio de verificación de usuarios
user_verification_service = get_user_verification_service()

# =============================================================================
# CONFIGURACIÓN DE LOGGING (REGISTRO DE EVENTOS)
# =============================================================================

# Configurar el sistema de logging para mostrar mensajes informativos
# level=logging.INFO significa que se mostrarán mensajes de nivel INFO y superiores
logging.basicConfig(level=logging.INFO)
# Crear un logger específico para este módulo
logger = logging.getLogger(__name__)

# Registrar las rutas de autenticación solo si OAuth está configurado
if oauth is not None:
    register_auth_routes(app, oauth, user_verification_service)
else:
    logger.warning("OAuth no configurado - las rutas de autenticación no están disponibles")


# =============================================================================
# FUNCIONES DE RATE LIMITING
# =============================================================================

def extract_rate_limit_headers(request):
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
    
    # Buscar el header x-ratelimit-info
    rate_limit_info = request.headers.get('x-ratelimit-info')
    if rate_limit_info:
        rate_limit_headers['x-ratelimit-info'] = rate_limit_info
        logger.info(f"Header de rate limiting encontrado: {rate_limit_info[:100]}...")
    else:
        logger.info("No se encontró header de rate limiting en la petición")
    
    return rate_limit_headers


# =============================================================================
# RUTAS DE LA APLICACIÓN WEB (ENDPOINTS)
# =============================================================================

@app.route('/')
def index():
    """
    Ruta principal de la aplicación.
    
    Esta ruta maneja la página de inicio y devuelve el template HTML
    que contiene el mapa interactivo y la interfaz de usuario.
    
    Returns:
        str: HTML renderizado del template index.html
    """
    # render_template busca el archivo en la carpeta 'templates/'
    # y lo procesa con el motor de templates de Flask (Jinja2)
    return render_template('index.html')

@app.route('/test')
def test_auth():
    """
    Ruta de prueba para el sistema de autenticación.
    
    Returns:
        str: HTML del archivo de prueba
    """
    with open('test_auth.html', 'r', encoding='utf-8') as f:
        return f.read()

# =============================================================================
# RUTAS DE LA API - SUCURSALES
# =============================================================================

@app.route('/api/sucursales', methods=['GET'])
@login_required
def get_sucursales():
    """
    Obtiene todas las sucursales desde la API externa.
    
    Esta ruta hace una petición a una API externa para obtener la lista
    de sucursales disponibles. No consulta la base de datos local.
    
    Returns:
        JSON: Lista de sucursales con sus datos (nombre, dirección, coordenadas, etc.)
        En caso de error: JSON con mensaje de error y código 500
    """
    try:
        # Extraer headers de rate limiting de la petición entrante
        rate_limit_headers = extract_rate_limit_headers(request)
        
        # Obtener el servicio de API externa configurado
        api_service = get_api_service()
        # Llamar al método que obtiene las sucursales de la API externa
        sucursales = api_service.get_subsidiaries(additional_headers=rate_limit_headers)
        # Convertir la lista de sucursales a formato JSON y devolverla
        return jsonify(sucursales)
    except Exception as e:
        # Si hay algún error, registrarlo en el log
        logger.error(f"Error al obtener sucursales: {str(e)}")
        # Devolver un error HTTP 500 (Error interno del servidor) con mensaje
        return jsonify({'error': 'Error al obtener sucursales desde la API externa'}), 500


# =============================================================================
# RUTAS DE LA API - ZONAS DE COBERTURA
# =============================================================================


@app.route('/api/zonas/<int:sucursal_id>', methods=['GET'])
@login_required
def get_zonas_sucursal(sucursal_id):
    """
    Obtiene las zonas de cobertura para una sucursal específica desde la API externa.
    
    Esta ruta hace una petición a la API externa para obtener las zonas
    de cobertura de una sucursal específica.
    
    Args:
        sucursal_id (int): ID de la sucursal para la cual obtener las zonas
    
    Returns:
        JSON: Lista de zonas de cobertura para la sucursal especificada
        En caso de error: JSON con mensaje de error y código 500
    """
    try:
        # Extraer headers de rate limiting de la petición entrante
        rate_limit_headers = extract_rate_limit_headers(request)
        
        # Obtener el servicio de API externa
        api_service = get_api_service()
        # Llamar al método que obtiene las zonas para una sucursal específica
        zonas = api_service.get_coverage_zones(sucursal_id, additional_headers=rate_limit_headers)
        # Devolver las zonas como JSON
        return jsonify(zonas)
    except Exception as e:
        # Registrar el error en el log
        logger.error(f"Error al obtener zonas para sucursal {sucursal_id}: {str(e)}")
        # Devolver error HTTP 500 con mensaje descriptivo
        return jsonify({'error': f'Error al obtener zonas de cobertura para la sucursal {sucursal_id}'}), 500


# =============================================================================
# RUTAS DE LA API - GEOCODIFICACIÓN
# =============================================================================

@app.route('/api/geocodificar', methods=['POST'])
@login_required
def geocodificar_direccion():
    """
    Geocodifica una dirección y obtiene sus coordenadas geográficas.
    
    La geocodificación es el proceso de convertir una dirección textual
    (como "Av. Corrientes 1234, Buenos Aires") en coordenadas geográficas
    (latitud y longitud) que se pueden usar en mapas.
    
    Returns:
        JSON: Coordenadas (latitud, longitud) y dirección completa encontrada
        En caso de error: JSON con mensaje de error y código correspondiente
    """
    # Obtener los datos JSON de la petición
    data = request.get_json()
    # Extraer la dirección del diccionario de datos
    direccion = data.get('direccion')
    
    # Validar que se haya proporcionado una dirección
    if not direccion:
        return jsonify({'error': 'Dirección requerida'}), 400
    
    try:
        # Crear un geocodificador usando el servicio Nominatim (gratuito)
        # user_agent es requerido para identificar nuestra aplicación
        geolocator = Nominatim(user_agent="zonas_cobertura_app")
        
        # Intentar geocodificar la dirección
        location = geolocator.geocode(direccion)
        
        if location:
            # Si se encontró la dirección, devolver las coordenadas
            return jsonify({
                'latitud': location.latitude,      # Coordenada Y (norte-sur)
                'longitud': location.longitude,    # Coordenada X (este-oeste)
                'direccion_completa': location.address  # Dirección completa encontrada
            })
        else:
            # Si no se pudo encontrar la dirección
            return jsonify({'error': 'No se pudo encontrar la dirección'}), 404
    except Exception as e:
        # Si hay algún error en el proceso de geocodificación
        return jsonify({'error': str(e)}), 500

# =============================================================================
# RUTAS DE LA API - CONSULTA DE COBERTURA
# =============================================================================



# =============================================================================
# RUTAS DE LA API - PROXY PARA API EXTERNA
# =============================================================================

@app.route('/internalapi/VerificarUsuarioAdmin', methods=['GET'])
@login_required
def proxy_verificar_usuario_admin():
    """
    Proxy para el endpoint VerificarUsuarioAdmin de la API externa.
    
    Esta ruta actúa como proxy para el endpoint /internalapi/VerificarUsuarioAdmin
    de la API externa, asegurando que los headers de rate limiting se envíen correctamente.
    
    Query Parameters:
        email (str): Email del usuario a verificar
    
    Returns:
        JSON: Resultado de la verificación del usuario
        En caso de error: JSON con mensaje de error y código correspondiente
    """
    try:
        # Obtener el email del query parameter
        email = request.args.get('email')
        
        if not email:
            return jsonify({'error': 'Parámetro email requerido'}), 400
        
        logger.info(f"Proxy: Verificando usuario admin: {email}")
        
        # Extraer headers de rate limiting de la petición entrante
        rate_limit_headers = extract_rate_limit_headers(request)
        
        # Verificar usuario contra la API externa usando el servicio
        verification_result = user_verification_service.verify_user(email, rate_limit_headers)
        
        if verification_result['registered']:
            logger.info(f"Proxy: Usuario verificado exitosamente: {email}")
            return jsonify({
                'registered': True,
                'user_data': verification_result['user_data']
            })
        else:
            logger.info(f"Proxy: Usuario no registrado: {email}")
            return jsonify({
                'registered': False,
                'error': 'Usuario no registrado en el sistema'
            }), 404
            
    except requests.RequestException as e:
        logger.error(f"Proxy: Error conectando con API externa: {str(e)}")
        return jsonify({
            'error': 'Error de conexión con el sistema de verificación'
        }), 500
        
    except Exception as e:
        logger.error(f"Proxy: Error verificando usuario: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

# =============================================================================
# RUTAS DE LA API - GUARDADO EN API EXTERNA
# =============================================================================

@app.route('/api/guardar-zona', methods=['POST'])
@login_required
def guardar_zona():
    """
    Guarda una zona de cobertura en la API externa.
    
    Esta ruta recibe los datos de una zona de cobertura y los envía
    a una API externa para su almacenamiento. Primero valida que
    todos los campos requeridos estén presentes.
    
    Returns:
        JSON: Mensaje de confirmación y datos de respuesta de la API externa
        En caso de error: JSON con mensaje de error y código correspondiente
    """
    try:
        # Obtener los datos JSON de la petición
        data = request.get_json()
        
        # =====================================================================
        # VALIDACIÓN DE DATOS REQUERIDOS
        # =====================================================================
        # Lista de campos que deben estar presentes en la petición
        required_fields = ['sucursal_id', 'nombre_zona', 'poligono_coordenadas']
        
        # Verificar que todos los campos requeridos estén presentes
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # =====================================================================
        # ENVÍO A API EXTERNA
        # =====================================================================
        # Extraer headers de rate limiting de la petición entrante
        rate_limit_headers = extract_rate_limit_headers(request)
        
        # Obtener el servicio de API externa
        api_service = get_api_service()
        # Enviar los datos a la API externa
        response = api_service.save_coverage_zone(data, additional_headers=rate_limit_headers)
        
        # Devolver respuesta exitosa con los datos de la API externa
        return jsonify({
            'message': 'Zona de cobertura guardada exitosamente',
            'data': response
        })
        
    except Exception as e:
        # Registrar el error en el log
        logger.error(f"Error al guardar zona de cobertura: {str(e)}")
        # Devolver error HTTP 500
        return jsonify({'error': 'Error al guardar zona de cobertura en la API externa'}), 500

@app.route('/api/eliminar-zona', methods=['DELETE'])
@login_required
def eliminar_zona():
    """
    Elimina una zona de cobertura de la API externa.
    
    Esta ruta recibe el ID de sucursal y el nombre de la zona a eliminar,
    y hace una petición DELETE a la API externa para eliminarla.
    
    Returns:
        JSON: Mensaje de confirmación y datos de respuesta de la API externa
        En caso de error: JSON con mensaje de error y código correspondiente
    """
    try:
        # Obtener los datos JSON de la petición
        data = request.get_json()
        
        # =====================================================================
        # VALIDACIÓN DE DATOS REQUERIDOS
        # =====================================================================
        # Lista de campos que deben estar presentes en la petición
        required_fields = ['sucursal_id', 'nombre_zona']
        
        # Verificar que todos los campos requeridos estén presentes
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # =====================================================================
        # ELIMINACIÓN EN API EXTERNA
        # =====================================================================
        # Extraer headers de rate limiting de la petición entrante
        rate_limit_headers = extract_rate_limit_headers(request)
        
        # Obtener el servicio de API externa
        api_service = get_api_service()
        # Enviar la petición de eliminación a la API externa
        response = api_service.delete_coverage_zone(
            sucursal_id=data['sucursal_id'],
            nombre_zona=data['nombre_zona'],
            additional_headers=rate_limit_headers
        )
        
        # Devolver respuesta exitosa con los datos de la API externa
        return jsonify({
            'message': 'Zona de cobertura eliminada exitosamente',
            'data': response
        })
        
    except Exception as e:
        # Registrar el error en el log
        logger.error(f"Error al eliminar zona de cobertura: {str(e)}")
        # Devolver error HTTP 500
        return jsonify({'error': 'Error al eliminar zona de cobertura en la API externa'}), 500

# =============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN
# =============================================================================

if __name__ == '__main__':
    """
    Punto de entrada principal de la aplicación.
    
    Esta sección se ejecuta solo cuando el archivo se ejecuta directamente
    (no cuando se importa como módulo). Arranca el servidor Flask.
    """
    # Iniciar el servidor Flask
    app.run(
        debug=True,        # Modo debug activado (recarga automática en cambios)
        host='0.0.0.0',    # Escuchar en todas las interfaces de red
        port=5000          # Puerto donde correrá la aplicación
    )
