# =============================================================================
# SERVICIO DE API EXTERNA - ZONAS DE COBERTURA
# =============================================================================
"""
Este módulo contiene la clase ExternalAPIService que se encarga de manejar
todas las comunicaciones con la API externa del sistema de sucursales.

Funcionalidades principales:
- Obtener lista de sucursales desde API externa
- Obtener zonas de cobertura para sucursales específicas
- Guardar nuevas zonas de cobertura en la API externa
- Manejo de errores y timeouts en peticiones HTTP
"""

# =============================================================================
# IMPORTS - Importación de librerías necesarias
# =============================================================================

# requests: Librería para hacer peticiones HTTP a APIs externas
import requests
# json: Para manejar datos en formato JSON
import json
# logging: Para registrar mensajes de log (errores, información, etc.)
import logging
# typing: Para definir tipos de datos (ayuda en el desarrollo y documentación)
from typing import List, Dict, Optional
# Config: Clase de configuración personalizada
from config import Config

# Crear un logger específico para este módulo
logger = logging.getLogger(__name__)

# =============================================================================
# CLASE PRINCIPAL - EXTERNALAPISERVICE
# =============================================================================

class ExternalAPIService:
    """
    Servicio para interactuar con la API externa de sucursales y zonas de cobertura.
    
    Esta clase encapsula toda la lógica de comunicación con la API externa,
    incluyendo autenticación, manejo de errores, y transformación de datos.
    
    Atributos:
        base_url (str): URL base de la API externa
        token (str): Token de autenticación para la API
        timeout (int): Tiempo límite para las peticiones HTTP
        headers (dict): Cabeceras HTTP para todas las peticiones
    """
    
    def __init__(self, config: Config):
        """
        Inicializa el servicio de API externa con la configuración proporcionada.
        
        Args:
            config (Config): Objeto de configuración que contiene los parámetros
                           de conexión a la API externa
        """
        # URL base de la API externa (ej: http://localhost:5064)
        self.base_url = config.EXTERNAL_API_BASE_URL
        
        # Token de autenticación para acceder a la API externa
        self.token = config.EXTERNAL_API_TOKEN
        
        # Tiempo límite en segundos para las peticiones HTTP
        self.timeout = config.EXTERNAL_API_TIMEOUT
        
        # Cabeceras HTTP que se enviarán con todas las peticiones
        self.headers = {
            'Authorization': f'Bearer {self.token}',  # Autenticación Bearer
            'Content-Type': 'application/json',       # Tipo de contenido que enviamos
            'Accept': 'application/json'              # Tipo de contenido que esperamos recibir
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Método privado que realiza una petición HTTP a la API externa.
        
        Este método centraliza toda la lógica de comunicación HTTP, incluyendo
        el manejo de diferentes métodos HTTP, timeouts, y errores.
        
        Args:
            method (str): Método HTTP a usar ('GET', 'POST', 'PUT', 'DELETE')
            endpoint (str): Endpoint de la API (ej: '/internalapi/SubsidiaryList/1')
            data (Optional[Dict]): Datos para enviar en el cuerpo de la petición
                                 (solo para POST/PUT, None para GET/DELETE)
            
        Returns:
            Dict: Respuesta de la API convertida a diccionario Python
            
        Raises:
            requests.RequestException: Si hay cualquier error en la petición HTTP
        """
        # Construir la URL completa combinando base_url y endpoint
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Registrar la petición en el log para debugging
            logger.info(f"Realizando petición {method} a {url}")
            
            # =====================================================================
            # EJECUTAR PETICIÓN HTTP SEGÚN EL MÉTODO
            # =====================================================================
            if method.upper() == 'GET':
                # Petición GET: solo obtener datos, sin cuerpo
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                # Petición POST: enviar datos en el cuerpo (json=data convierte a JSON automáticamente)
                response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
            elif method.upper() == 'PUT':
                # Petición PUT: actualizar datos existentes
                response = requests.put(url, headers=self.headers, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                # Petición DELETE: eliminar datos
                response = requests.delete(url, headers=self.headers, timeout=self.timeout)
            else:
                # Método HTTP no soportado
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            # =====================================================================
            # VERIFICAR RESPUESTA HTTP
            # =====================================================================
            # raise_for_status() lanza una excepción si el código de estado HTTP
            # indica un error (400, 500, etc.)
            response.raise_for_status()
            
            # Convertir la respuesta JSON a un diccionario Python
            return response.json()
            
        # =====================================================================
        # MANEJO DE ERRORES ESPECÍFICOS
        # =====================================================================
        except requests.exceptions.Timeout:
            # Error de timeout: la API tardó demasiado en responder
            logger.error(f"Timeout al conectar con la API externa: {url}")
            raise requests.RequestException("Timeout al conectar con la API externa")
            
        except requests.exceptions.ConnectionError:
            # Error de conexión: no se pudo conectar a la API
            logger.error(f"Error de conexión con la API externa: {url}")
            raise requests.RequestException("Error de conexión con la API externa")
            
        except requests.exceptions.HTTPError as e:
            # Error HTTP: la API devolvió un código de error (400, 500, etc.)
            logger.error(f"Error HTTP {e.response.status_code} al llamar a {url}: {e.response.text}")
            raise requests.RequestException(f"Error HTTP {e.response.status_code}: {e.response.text}")
            
        except json.JSONDecodeError:
            # Error al decodificar JSON: la respuesta no es JSON válido
            logger.error(f"Error al decodificar respuesta JSON de {url}")
            raise requests.RequestException("Error al decodificar respuesta JSON")
            
        except Exception as e:
            # Cualquier otro error inesperado
            logger.error(f"Error inesperado al llamar a {url}: {str(e)}")
            raise requests.RequestException(f"Error inesperado: {str(e)}")
    
    # =============================================================================
    # MÉTODOS PÚBLICOS - FUNCIONALIDADES PRINCIPALES
    # =============================================================================
    
    def get_subsidiaries(self) -> List[Dict]:
        """
        Obtiene la lista completa de sucursales desde la API externa.
        
        Este método hace una petición GET a la API externa para obtener
        todas las sucursales disponibles. Los datos se normalizan para
        que tengan un formato consistente independientemente de cómo
        los devuelva la API externa.
        
        Returns:
            List[Dict]: Lista de diccionarios, cada uno representando una sucursal
                       con los campos: id, nombre, direccion, latitud, longitud,
                       ciudad, telefonos, pedidosYaClienteID, activa
        
        Raises:
            requests.RequestException: Si hay un error al comunicarse con la API externa
        """
        try:
            # Hacer petición GET al endpoint de lista de sucursales
            response = self._make_request('GET', Config.SUBSIDIARY_LIST_ENDPOINT)
            
            # =====================================================================
            # NORMALIZACIÓN DE DATOS
            # =====================================================================
            # La API externa puede devolver datos en un formato diferente
            # al que espera nuestra aplicación, por lo que los normalizamos
            subsidiaries = []
            for item in response:
                # Crear diccionario con formato estándar para cada sucursal
                subsidiary = {
                    'id': item.get('sucursalId'),                    # ID de la sucursal
                    'nombre': item.get('nombre'),                    # Nombre de la sucursal
                    'direccion': item.get('direccion', ''),  # Dirección completa
                    'latitud': item.get('latitud'),                  # Coordenada de latitud
                    'longitud': item.get('longitud'),                # Coordenada de longitud
                    'ciudad': item.get('ciudad'),                    # Ciudad donde está ubicada
                    'telefonos': item.get('telefonos'),              # Números de teléfono
                    'pedidosYaClienteID': item.get('pedidosYaClienteID'),  # ID para PedidosYa
                    'activa': True  # Asumimos que todas las sucursales de la API están activas
                }
                subsidiaries.append(subsidiary)
            
            # Registrar en el log cuántas sucursales se obtuvieron
            logger.info(f"Se obtuvieron {len(subsidiaries)} sucursales de la API externa")
            return subsidiaries
            
        except Exception as e:
            # Si hay algún error, registrarlo y re-lanzarlo
            logger.error(f"Error al obtener sucursales: {str(e)}")
            raise
    
    def get_coverage_zones(self, subsidiary_id: int) -> List[Dict]:
        """
        Obtiene las zonas de cobertura para una sucursal específica.
        
        Este método consulta la API externa para obtener todas las zonas
        de cobertura (áreas de delivery) asociadas a una sucursal particular.
        
        Args:
            subsidiary_id (int): ID de la sucursal para la cual obtener las zonas
        
        Returns:
            List[Dict]: Lista de diccionarios, cada uno representando una zona
                       con los campos: id, sucursal_id, nombre_zona, poligono_coordenadas,
                       fecha_creacion, activa, calles
        
        Raises:
            requests.RequestException: Si hay un error al comunicarse con la API externa
        """
        try:
            # Construir el endpoint específico para la sucursal
            # Ejemplo: '/internalapi/ZonasDeCobertura/123'
            endpoint = f"{Config.ZONAS_COBERTURA_ENDPOINT}/{subsidiary_id}"
            
            # Hacer petición GET al endpoint de zonas de cobertura
            response = self._make_request('GET', endpoint)
            
            # =====================================================================
            # NORMALIZACIÓN DE DATOS DE ZONAS
            # =====================================================================
            # La API externa devuelve un objeto con la propiedad 'zonasCobertura'
            # que contiene la lista de zonas
            zonas_data = response.get('zonasCobertura', [])
            
            zones = []
            for item in zonas_data:
                # Crear diccionario con formato estándar para cada zona
                zone = {
                    'id': item.get('zonaId'),                    # ID de la zona
                    'sucursal_id': subsidiary_id,                # ID de la sucursal (lo pasamos como parámetro)
                    'nombre_zona': item.get('nombreZona'),       # Nombre descriptivo de la zona
                    'poligono_coordenadas': item.get('poligonoCoordenadas'),  # Coordenadas del polígono
                    'fecha_creacion': item.get('fechaCreacion'), # Cuándo se creó la zona
                    'activa': item.get('activa', True),          # Si la zona está activa (por defecto True)
                }
                
                # Logging detallado para debug de coordenadas
                logger.info(f"=== RECIBIENDO ZONA DE API EXTERNA ===")
                logger.info(f"Zona: {zone['nombre_zona']}")
                logger.info(f"Coordenadas recibidas: {zone['poligono_coordenadas']}")
                logger.info(f"Tipo de coordenadas: {type(zone['poligono_coordenadas'])}")
                if isinstance(zone['poligono_coordenadas'], list) and len(zone['poligono_coordenadas']) > 0:
                    logger.info(f"Primera coordenada: {zone['poligono_coordenadas'][0]}")
                    logger.info(f"Última coordenada: {zone['poligono_coordenadas'][-1]}")
                elif isinstance(zone['poligono_coordenadas'], str):
                    try:
                        parsed_coords = json.loads(zone['poligono_coordenadas'])
                        logger.info(f"Coordenadas parseadas: {parsed_coords}")
                        if isinstance(parsed_coords, list) and len(parsed_coords) > 0:
                            logger.info(f"Primera coordenada parseada: {parsed_coords[0]}")
                            logger.info(f"Última coordenada parseada: {parsed_coords[-1]}")
                    except json.JSONDecodeError:
                        logger.error(f"Error parseando coordenadas JSON: {zone['poligono_coordenadas']}")
                
                zones.append(zone)
            
            # Registrar en el log cuántas zonas se obtuvieron
            logger.info(f"Se obtuvieron {len(zones)} zonas de cobertura para la sucursal {subsidiary_id}")
            return zones
            
        except Exception as e:
            # Si hay algún error, registrarlo y re-lanzarlo
            logger.error(f"Error al obtener zonas de cobertura para sucursal {subsidiary_id}: {str(e)}")
            raise
    
    def save_coverage_zone(self, zone_data: Dict) -> Dict:
        """
        Guarda una nueva zona de cobertura en la API externa.
        
        Este método envía los datos de una zona de cobertura a la API externa
        para que sea almacenada. Los datos se transforman al formato esperado
        por la API externa antes de ser enviados.
        
        Args:
            zone_data (Dict): Diccionario con los datos de la zona a guardar
                             Debe contener: sucursal_id, nombre_zona, poligono_coordenadas,
                             calles (opcional), activa (opcional)
        
        Returns:
            Dict: Respuesta de la API externa con el resultado del guardado
                 (generalmente contiene el ID de la zona creada)
        
        Raises:
            requests.RequestException: Si hay un error al comunicarse con la API externa
        """
        try:
            # =====================================================================
            # TRANSFORMACIÓN DE DATOS AL FORMATO DE LA API EXTERNA
            # =====================================================================
            # La API externa espera los datos en un formato específico,
            # por lo que transformamos nuestros datos internos
            api_data = {
                'sucursalId': zone_data.get('sucursal_id'),              # ID de la sucursal
                'nombreZona': zone_data.get('nombre_zona'),              # Nombre de la zona
                'poligonoCoordenadas': zone_data.get('poligono_coordenadas'),  # Coordenadas del polígono
                'activa': zone_data.get('activa', True),                 # Estado activo (por defecto True)
                'calles': zone_data.get('calles', [])                    # Lista de calles (requerido por la API externa)
            }
            
            # Logging detallado para debug de coordenadas
            logger.info(f"=== ENVIANDO ZONA A API EXTERNA ===")
            logger.info(f"Zona: {api_data['nombreZona']}")
            logger.info(f"Coordenadas enviadas: {api_data['poligonoCoordenadas']}")
            logger.info(f"Tipo de coordenadas: {type(api_data['poligonoCoordenadas'])}")
            if isinstance(api_data['poligonoCoordenadas'], list) and len(api_data['poligonoCoordenadas']) > 0:
                logger.info(f"Primera coordenada: {api_data['poligonoCoordenadas'][0]}")
                logger.info(f"Última coordenada: {api_data['poligonoCoordenadas'][-1]}")
            
            # Hacer petición POST al endpoint de guardado de zonas
            response = self._make_request('POST', Config.GUARDAR_ZONA_ENDPOINT, api_data)
            
            # Registrar en el log que la zona se guardó exitosamente
            logger.info(f"Zona de cobertura guardada exitosamente: {response}")
            return response
            
        except Exception as e:
            # Si hay algún error, registrarlo y re-lanzarlo
            logger.error(f"Error al guardar zona de cobertura: {str(e)}")
            raise
    
    def delete_coverage_zone(self, sucursal_id: int, nombre_zona: str) -> Dict:
        """
        Elimina una zona de cobertura de la API externa.
        
        Este método envía una petición DELETE a la API externa para eliminar
        una zona de cobertura específica identificada por el ID de sucursal
        y el nombre de la zona.
        
        Args:
            sucursal_id (int): ID de la sucursal a la que pertenece la zona
            nombre_zona (str): Nombre de la zona a eliminar
        
        Returns:
            Dict: Respuesta de la API externa con el resultado de la eliminación
        
        Raises:
            requests.RequestException: Si hay un error al comunicarse con la API externa
        """
        try:
            # Construir el endpoint específico para la eliminación
            # Formato: /internalapi/EliminarZonaCobertura/{sucursalId}/{nombreZona}
            endpoint = f"{Config.ELIMINAR_ZONA_ENDPOINT}/{sucursal_id}/{nombre_zona}"
            
            # Hacer petición DELETE al endpoint de eliminación
            response = self._make_request('DELETE', endpoint)
            
            # Registrar en el log que la zona se eliminó exitosamente
            logger.info(f"Zona de cobertura eliminada exitosamente: sucursal_id={sucursal_id}, nombre_zona={nombre_zona}")
            return response
            
        except Exception as e:
            # Si hay algún error, registrarlo y re-lanzarlo
            logger.error(f"Error al eliminar zona de cobertura: sucursal_id={sucursal_id}, nombre_zona={nombre_zona}, error={str(e)}")
            raise

# =============================================================================
# FUNCIÓN DE INICIALIZACIÓN GLOBAL
# =============================================================================

# Variable global para almacenar la instancia del servicio
# Esto implementa el patrón Singleton para evitar crear múltiples instancias
api_service = None

def get_api_service() -> ExternalAPIService:
    """
    Obtiene la instancia única del servicio de API externa (patrón Singleton).
    
    Esta función implementa el patrón Singleton para asegurar que solo
    exista una instancia del servicio de API externa en toda la aplicación.
    Si la instancia no existe, la crea usando la configuración por defecto.
    
    Returns:
        ExternalAPIService: Instancia única del servicio de API externa
    """
    global api_service
    
    # Si no existe la instancia, crearla
    if api_service is None:
        # Importar la configuración (se hace aquí para evitar importaciones circulares)
        from config import config
        # Crear nueva instancia usando la configuración por defecto
        api_service = ExternalAPIService(config['default'])
    
    # Devolver la instancia (existente o recién creada)
    return api_service
