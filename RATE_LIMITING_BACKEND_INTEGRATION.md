# Integración de Rate Limiting en el Backend Flask

## Problema Identificado

El header `x-ratelimit-info` enviado desde el frontend solo llegaba a la API intermedia (Flask), pero no se estaba reenviando al backend de .NET que tiene el middleware de rate limiting implementado.

## Solución Implementada

### 1. Modificaciones en `api_service.py`

#### **Método `_make_request` actualizado:**
- Agregado parámetro `additional_headers` para recibir headers adicionales
- Combinación de headers base con headers adicionales (rate limiting)
- Logging de headers adicionales para debugging

```python
def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, additional_headers: Optional[Dict] = None) -> Dict:
    # Combinar headers base con headers adicionales
    headers = self.headers.copy()
    if additional_headers:
        headers.update(additional_headers)
        logger.info(f"Headers adicionales incluidos: {list(additional_headers.keys())}")
```

#### **Métodos públicos actualizados:**
Todos los métodos públicos ahora aceptan y reenvían headers adicionales:

- `get_subsidiaries(additional_headers=None)`
- `get_coverage_zones(subsidiary_id, additional_headers=None)`
- `save_coverage_zone(zone_data, additional_headers=None)`
- `delete_coverage_zone(sucursal_id, nombre_zona, additional_headers=None)`

### 2. Modificaciones en `app.py`

#### **Nueva función `extract_rate_limit_headers`:**
```python
def extract_rate_limit_headers(request):
    """
    Extrae los headers de rate limiting de la petición entrante.
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
```

#### **Rutas de API actualizadas:**
Todas las rutas que se comunican con la API externa ahora:

1. **Extraen** el header `x-ratelimit-info` de la petición entrante
2. **Reenvían** el header a la API externa (.NET backend)

**Rutas modificadas:**
- `GET /api/sucursales` - Obtener sucursales
- `GET /api/zonas/<sucursal_id>` - Obtener zonas de sucursal
- `POST /api/guardar-zona` - Guardar zona
- `DELETE /api/eliminar-zona` - Eliminar zona

### 3. Flujo de Rate Limiting Completo

```
Frontend (JavaScript)
    ↓ (envía x-ratelimit-info)
API Intermedia (Flask)
    ↓ (extrae y reenvía x-ratelimit-info)
Backend .NET (con middleware de rate limiting)
    ↓ (procesa rate limiting y responde)
API Intermedia (Flask)
    ↓ (devuelve respuesta)
Frontend (JavaScript)
    ↓ (actualiza indicador de rate limiting)
```

## Características de la Implementación

### **Transparencia:**
- El sistema funciona de forma transparente
- No requiere cambios en la lógica de negocio existente
- Mantiene compatibilidad con peticiones sin rate limiting

### **Logging Detallado:**
- Registra cuando se encuentran headers de rate limiting
- Muestra qué headers adicionales se están reenviando
- Facilita el debugging y monitoreo

### **Manejo de Errores:**
- Si no hay header de rate limiting, la petición continúa normalmente
- Los errores de rate limiting se propagan correctamente
- Mantiene la funcionalidad existente intacta

## Endpoints Afectados

| Endpoint | Método | Descripción | Rate Limiting |
|----------|--------|-------------|---------------|
| `/api/sucursales` | GET | Obtener sucursales | ✅ Reenviado |
| `/api/zonas/<id>` | GET | Obtener zonas de sucursal | ✅ Reenviado |
| `/api/guardar-zona` | POST | Guardar zona | ✅ Reenviado |
| `/api/eliminar-zona` | DELETE | Eliminar zona | ✅ Reenviado |
| `/api/zonas` | GET | Obtener todas las zonas | ❌ Solo local |
| `/api/consultar-cobertura` | POST | Consultar cobertura | ❌ Solo local |

## Testing

Para verificar que la integración funciona correctamente:

1. **Verificar logs del servidor Flask:**
   ```
   INFO: Header de rate limiting encontrado: {"ClientIP":"192.168.1.123"...
   INFO: Headers adicionales incluidos: ['x-ratelimit-info']
   ```

2. **Verificar logs del backend .NET:**
   - El middleware debería recibir y procesar el header `x-ratelimit-info`
   - Debería devolver headers de respuesta de rate limiting

3. **Verificar frontend:**
   - El indicador de rate limiting debería actualizarse
   - Los errores 429 deberían manejarse correctamente

## Consideraciones de Producción

### **Performance:**
- El overhead de extraer y reenviar headers es mínimo
- No afecta la funcionalidad existente

### **Seguridad:**
- Los headers se reenvían tal como se reciben
- No se modifican ni validan (responsabilidad del backend .NET)

### **Monitoreo:**
- Los logs permiten monitorear el flujo de rate limiting
- Facilita la detección de problemas de integración

## Compatibilidad

- ✅ **Backward Compatible:** Funciona con peticiones sin rate limiting
- ✅ **Frontend Compatible:** No requiere cambios en el frontend
- ✅ **Backend Compatible:** Compatible con el middleware .NET existente
- ✅ **API Compatible:** Mantiene la interfaz de API existente
