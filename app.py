# =============================================================================
# IMPORTS - Importación de librerías y módulos necesarios
# =============================================================================

# Flask: Framework web para crear aplicaciones web en Python
from flask import Flask, request, jsonify, render_template
# CORS: Permite que el navegador haga peticiones desde diferentes dominios
from flask_cors import CORS
# sqlite3: Base de datos SQLite integrada en Python (no necesita servidor separado)
import sqlite3
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

# =============================================================================
# CONFIGURACIÓN INICIAL DE LA APLICACIÓN FLASK
# =============================================================================

# Crear la instancia de la aplicación Flask
# __name__ es una variable especial de Python que contiene el nombre del módulo actual
app = Flask(__name__)

# Habilitar CORS (Cross-Origin Resource Sharing) para permitir peticiones desde el frontend
# Esto es necesario cuando el frontend y backend están en diferentes puertos/dominios
CORS(app)

# =============================================================================
# CONFIGURACIÓN DE LOGGING (REGISTRO DE EVENTOS)
# =============================================================================

# Configurar el sistema de logging para mostrar mensajes informativos
# level=logging.INFO significa que se mostrarán mensajes de nivel INFO y superiores
logging.basicConfig(level=logging.INFO)
# Crear un logger específico para este módulo
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================================================

# Nombre del archivo de base de datos SQLite
# SQLite es una base de datos ligera que se almacena en un archivo
DATABASE = 'zonas_cobertura.db'

# =============================================================================
# FUNCIONES DE BASE DE DATOS
# =============================================================================

def init_db():
    """
    Inicializa la base de datos SQLite creando las tablas necesarias si no existen.
    
    Esta función se ejecuta al iniciar la aplicación y crea tres tablas principales:
    1. sucursales: Almacena información de las sucursales (nombre, dirección, coordenadas)
    2. zonas_cobertura: Almacena las zonas de cobertura dibujadas en el mapa
    3. calles_cobertura: Almacena las calles y rangos de altura para cada zona
    """
    # Conectar a la base de datos SQLite
    # Si el archivo no existe, SQLite lo crea automáticamente
    conn = sqlite3.connect(DATABASE)
    # Crear un cursor para ejecutar comandos SQL
    cursor = conn.cursor()
    
    # =====================================================================
    # TABLA DE SUCURSALES
    # =====================================================================
    # Almacena información básica de cada sucursal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sucursales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único autoincremental
            nombre TEXT NOT NULL,                  -- Nombre de la sucursal
            direccion TEXT NOT NULL,               -- Dirección completa
            latitud REAL NOT NULL,                 -- Coordenada de latitud (Y)
            longitud REAL NOT NULL,                -- Coordenada de longitud (X)
            activa BOOLEAN DEFAULT 1               -- Si la sucursal está activa (1=si, 0=no)
        )
    ''')
    
    # =====================================================================
    # TABLA DE ZONAS DE COBERTURA
    # =====================================================================
    # Almacena las zonas dibujadas en el mapa para cada sucursal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zonas_cobertura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único autoincremental
            sucursal_id INTEGER NOT NULL,          -- ID de la sucursal a la que pertenece
            nombre_zona TEXT NOT NULL,             -- Nombre descriptivo de la zona
            poligono_coordenadas TEXT NOT NULL,    -- Coordenadas del polígono en formato JSON
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Cuándo se creó
            activa BOOLEAN DEFAULT 1,              -- Si la zona está activa
            FOREIGN KEY (sucursal_id) REFERENCES sucursales (id)  -- Relación con sucursales
        )
    ''')
    
    # =====================================================================
    # TABLA DE CALLES EN ZONAS DE COBERTURA
    # =====================================================================
    # Almacena las calles y rangos de altura para cada zona
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calles_cobertura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único autoincremental
            zona_id INTEGER NOT NULL,              -- ID de la zona a la que pertenece
            nombre_calle TEXT NOT NULL,            -- Nombre de la calle
            altura_desde INTEGER NOT NULL,         -- Altura mínima de la calle
            altura_hasta INTEGER NOT NULL,         -- Altura máxima de la calle
            FOREIGN KEY (zona_id) REFERENCES zonas_cobertura (id)  -- Relación con zonas
        )
    ''')
    
    # Confirmar los cambios en la base de datos
    conn.commit()
    # Cerrar la conexión para liberar recursos
    conn.close()

def get_db_connection():
    """
    Obtiene una conexión a la base de datos SQLite.
    
    Returns:
        sqlite3.Connection: Conexión configurada para devolver filas como diccionarios
    """
    # Conectar a la base de datos
    conn = sqlite3.connect(DATABASE)
    # Configurar para que las filas se devuelvan como diccionarios
    # Esto permite acceder a los datos por nombre de columna: row['nombre']
    conn.row_factory = sqlite3.Row
    return conn

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

# =============================================================================
# RUTAS DE LA API - SUCURSALES
# =============================================================================

@app.route('/api/sucursales', methods=['GET'])
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
        # Obtener el servicio de API externa configurado
        api_service = get_api_service()
        # Llamar al método que obtiene las sucursales de la API externa
        sucursales = api_service.get_subsidiaries()
        # Convertir la lista de sucursales a formato JSON y devolverla
        return jsonify(sucursales)
    except Exception as e:
        # Si hay algún error, registrarlo en el log
        logger.error(f"Error al obtener sucursales: {str(e)}")
        # Devolver un error HTTP 500 (Error interno del servidor) con mensaje
        return jsonify({'error': 'Error al obtener sucursales desde la API externa'}), 500

@app.route('/api/sucursales', methods=['POST'])
def create_sucursal():
    """
    Crea una nueva sucursal en la base de datos local.
    
    Esta ruta recibe los datos de una nueva sucursal (nombre, dirección, coordenadas)
    y la guarda en la base de datos SQLite local.
    
    Returns:
        JSON: ID de la sucursal creada y mensaje de confirmación
    """
    # Obtener los datos JSON enviados en el cuerpo de la petición
    data = request.get_json()
    
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insertar la nueva sucursal en la tabla 'sucursales'
    # Los ? son placeholders que se reemplazan con los valores de la tupla
    cursor.execute('''
        INSERT INTO sucursales (nombre, direccion, latitud, longitud)
        VALUES (?, ?, ?, ?)
    ''', (data['nombre'], data['direccion'], data['latitud'], data['longitud']))
    
    # Obtener el ID de la sucursal recién creada
    sucursal_id = cursor.lastrowid
    
    # Confirmar los cambios en la base de datos
    conn.commit()
    # Cerrar la conexión
    conn.close()
    
    # Devolver respuesta exitosa con el ID de la sucursal creada
    return jsonify({'id': sucursal_id, 'message': 'Sucursal creada exitosamente'})

# =============================================================================
# RUTAS DE LA API - ZONAS DE COBERTURA
# =============================================================================

@app.route('/api/zonas', methods=['GET'])
def get_zonas():
    """
    Obtiene todas las zonas de cobertura desde la base de datos local.
    
    Esta ruta consulta la base de datos SQLite local para obtener todas las zonas
    de cobertura activas, incluyendo el nombre de la sucursal a la que pertenecen.
    
    Returns:
        JSON: Lista de zonas de cobertura con información de sucursales
    """
    # Conectar a la base de datos
    conn = get_db_connection()
    
    # Consulta SQL que une las tablas 'zonas_cobertura' y 'sucursales'
    # para obtener el nombre de la sucursal junto con los datos de la zona
    zonas = conn.execute('''
        SELECT z.*, s.nombre as sucursal_nombre 
        FROM zonas_cobertura z
        JOIN sucursales s ON z.sucursal_id = s.id
        WHERE z.activa = 1
    ''').fetchall()
    
    # Cerrar la conexión
    conn.close()
    
    # Convertir cada fila (que es un objeto Row) a un diccionario
    # y devolver la lista como JSON
    return jsonify([dict(zona) for zona in zonas])

@app.route('/api/zonas/<int:sucursal_id>', methods=['GET'])
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
        # Obtener el servicio de API externa
        api_service = get_api_service()
        # Llamar al método que obtiene las zonas para una sucursal específica
        zonas = api_service.get_coverage_zones(sucursal_id)
        # Devolver las zonas como JSON
        return jsonify(zonas)
    except Exception as e:
        # Registrar el error en el log
        logger.error(f"Error al obtener zonas para sucursal {sucursal_id}: {str(e)}")
        # Devolver error HTTP 500 con mensaje descriptivo
        return jsonify({'error': f'Error al obtener zonas de cobertura para la sucursal {sucursal_id}'}), 500

@app.route('/api/zonas', methods=['POST'])
def create_zona():
    """
    Crea una nueva zona de cobertura en la base de datos local.
    
    Esta ruta recibe los datos de una nueva zona de cobertura (sucursal_id,
    nombre_zona, polígono_coordenadas) y la guarda en la base de datos SQLite.
    
    Returns:
        JSON: ID de la zona creada y mensaje de confirmación
    """
    # Obtener los datos JSON enviados en el cuerpo de la petición
    data = request.get_json()
    
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insertar la nueva zona en la tabla 'zonas_cobertura'
    # json.dumps() convierte la lista de coordenadas a una cadena JSON
    cursor.execute('''
        INSERT INTO zonas_cobertura (sucursal_id, nombre_zona, poligono_coordenadas)
        VALUES (?, ?, ?)
    ''', (data['sucursal_id'], data['nombre_zona'], json.dumps(data['poligono_coordenadas'])))
    
    # Obtener el ID de la zona recién creada
    zona_id = cursor.lastrowid
    
    # Confirmar los cambios y cerrar la conexión
    conn.commit()
    conn.close()
    
    # Devolver respuesta exitosa
    return jsonify({'id': zona_id, 'message': 'Zona creada exitosamente'})

# =============================================================================
# RUTAS DE LA API - GEOCODIFICACIÓN
# =============================================================================

@app.route('/api/geocodificar', methods=['POST'])
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

@app.route('/api/consultar-cobertura', methods=['POST'])
def consultar_cobertura():
    """
    Consulta si una dirección está dentro de alguna zona de cobertura.
    
    Esta es una de las funciones más importantes de la aplicación. Realiza los siguientes pasos:
    1. Geocodifica la dirección para obtener coordenadas
    2. Busca todas las zonas de cobertura activas en la base de datos
    3. Verifica si las coordenadas están dentro de algún polígono de zona
    4. Devuelve información sobre las zonas que cubren esa dirección
    
    Returns:
        JSON: Información sobre la dirección y las zonas que la cubren
        En caso de error: JSON con mensaje de error y código correspondiente
    """
    # Obtener los datos JSON de la petición
    data = request.get_json()
    direccion = data.get('direccion')
    
    # Validar que se haya proporcionado una dirección
    if not direccion:
        return jsonify({'error': 'Dirección requerida'}), 400
    
    try:
        # =====================================================================
        # PASO 1: GEOCODIFICAR LA DIRECCIÓN
        # =====================================================================
        # Crear geocodificador y convertir dirección a coordenadas
        geolocator = Nominatim(user_agent="zonas_cobertura_app")
        location = geolocator.geocode(direccion)
        
        # Si no se pudo encontrar la dirección, devolver error
        if not location:
            return jsonify({'error': 'No se pudo encontrar la dirección'}), 404
        
        # =====================================================================
        # PASO 2: CREAR PUNTO GEOMÉTRICO
        # =====================================================================
        # Crear un punto geométrico con las coordenadas encontradas
        # Nota: Point(longitud, latitud) - el orden es importante
        punto = Point(location.longitude, location.latitude)
        
        # =====================================================================
        # PASO 3: BUSCAR ZONAS DE COBERTURA
        # =====================================================================
        # Conectar a la base de datos y obtener todas las zonas activas
        conn = get_db_connection()
        zonas = conn.execute('''
            SELECT z.*, s.nombre as sucursal_nombre 
            FROM zonas_cobertura z
            JOIN sucursales s ON z.sucursal_id = s.id
            WHERE z.activa = 1
        ''').fetchall()
        
        # =====================================================================
        # PASO 4: VERIFICAR SI EL PUNTO ESTÁ EN ALGUNA ZONA
        # =====================================================================
        zonas_encontradas = []
        for zona in zonas:
            # Convertir las coordenadas JSON a una lista de coordenadas
            coordenadas = json.loads(zona['poligono_coordenadas'])
            # Crear un polígono con esas coordenadas
            poligono = Polygon(coordenadas)
            
            # Verificar si el punto está dentro del polígono
            if poligono.contains(punto):
                # Si está dentro, agregar información de la zona
                zonas_encontradas.append({
                    'zona_id': zona['id'],
                    'nombre_zona': zona['nombre_zona'],
                    'sucursal_nombre': zona['sucursal_nombre'],
                    'sucursal_id': zona['sucursal_id']
                })
        
        # Cerrar la conexión a la base de datos
        conn.close()
        
        # =====================================================================
        # PASO 5: DEVOLVER RESULTADO
        # =====================================================================
        return jsonify({
            'direccion': location.address,                    # Dirección completa encontrada
            'coordenadas': {                                  # Coordenadas de la dirección
                'latitud': location.latitude,
                'longitud': location.longitude
            },
            'en_zona_cobertura': len(zonas_encontradas) > 0,  # True si está en alguna zona
            'zonas': zonas_encontradas                        # Lista de zonas que cubren la dirección
        })
        
    except Exception as e:
        # Si hay algún error durante el proceso, devolverlo
        return jsonify({'error': str(e)}), 500

# =============================================================================
# RUTAS DE LA API - GESTIÓN DE CALLES
# =============================================================================

@app.route('/api/obtener-calles-zona', methods=['POST'])
def obtener_calles_zona():
    """
    Obtiene las calles y rangos de altura para una zona de cobertura específica.
    
    Esta ruta consulta la base de datos para obtener todas las calles
    que están asociadas a una zona de cobertura, incluyendo los rangos
    de altura (desde-hasta) para cada calle.
    
    Returns:
        JSON: Lista de calles con sus rangos de altura
        En caso de error: JSON con mensaje de error y código 400
    """
    # Obtener los datos JSON de la petición
    data = request.get_json()
    zona_id = data.get('zona_id')
    
    # Validar que se haya proporcionado un ID de zona
    if not zona_id:
        return jsonify({'error': 'ID de zona requerido'}), 400
    
    # Conectar a la base de datos
    conn = get_db_connection()
    
    # Consultar todas las calles asociadas a la zona especificada
    calles = conn.execute('''
        SELECT * FROM calles_cobertura WHERE zona_id = ?
    ''', (zona_id,)).fetchall()
    
    # Cerrar la conexión
    conn.close()
    
    # Convertir las filas a diccionarios y devolver como JSON
    return jsonify([dict(calle) for calle in calles])

@app.route('/api/guardar-calles-zona', methods=['POST'])
def guardar_calles_zona():
    """
    Guarda las calles y rangos de altura para una zona de cobertura.
    
    Esta ruta recibe una lista de calles con sus rangos de altura y las
    guarda en la base de datos. Primero elimina las calles existentes
    para la zona y luego inserta las nuevas.
    
    Returns:
        JSON: Mensaje de confirmación del guardado
        En caso de error: JSON con mensaje de error y código 400
    """
    # Obtener los datos JSON de la petición
    data = request.get_json()
    zona_id = data.get('zona_id')
    calles = data.get('calles', [])  # Lista de calles, por defecto lista vacía
    
    # Validar que se haya proporcionado un ID de zona
    if not zona_id:
        return jsonify({'error': 'ID de zona requerido'}), 400
    
    # Conectar a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # =====================================================================
    # PASO 1: ELIMINAR CALLES EXISTENTES
    # =====================================================================
    # Eliminar todas las calles existentes para esta zona
    # Esto permite reemplazar completamente la lista de calles
    cursor.execute('DELETE FROM calles_cobertura WHERE zona_id = ?', (zona_id,))
    
    # =====================================================================
    # PASO 2: INSERTAR NUEVAS CALLES
    # =====================================================================
    # Recorrer la lista de calles y insertar cada una
    for calle in calles:
        cursor.execute('''
            INSERT INTO calles_cobertura (zona_id, nombre_calle, altura_desde, altura_hasta)
            VALUES (?, ?, ?, ?)
        ''', (zona_id, calle['nombre_calle'], calle['altura_desde'], calle['altura_hasta']))
    
    # Confirmar todos los cambios en la base de datos
    conn.commit()
    # Cerrar la conexión
    conn.close()
    
    # Devolver mensaje de confirmación
    return jsonify({'message': 'Calles guardadas exitosamente'})

# =============================================================================
# RUTAS DE LA API - GUARDADO EN API EXTERNA
# =============================================================================

@app.route('/api/guardar-zona', methods=['POST'])
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
        # Obtener el servicio de API externa
        api_service = get_api_service()
        # Enviar los datos a la API externa
        response = api_service.save_coverage_zone(data)
        
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

# =============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN
# =============================================================================

if __name__ == '__main__':
    """
    Punto de entrada principal de la aplicación.
    
    Esta sección se ejecuta solo cuando el archivo se ejecuta directamente
    (no cuando se importa como módulo). Inicializa la base de datos
    y arranca el servidor Flask.
    """
    # Inicializar la base de datos (crear tablas si no existen)
    init_db()
    
    # Iniciar el servidor Flask
    app.run(
        debug=True,        # Modo debug activado (recarga automática en cambios)
        host='0.0.0.0',    # Escuchar en todas las interfaces de red
        port=5000          # Puerto donde correrá la aplicación
    )
