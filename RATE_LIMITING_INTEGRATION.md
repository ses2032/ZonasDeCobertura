# Integración de Rate Limiting en el Frontend

## Resumen

Se ha implementado la integración completa del sistema de rate limiting en el frontend para trabajar correctamente con el middleware de rate limiting del backend.

## Características Implementadas

### 1. Generación de RateLimitInfo
- **Session ID**: Generado automáticamente al cargar la página
- **Client Fingerprint**: Basado en características del navegador y dispositivo
- **Client IP**: Simulada para desarrollo (en producción vendría del servidor)
- **Timestamp**: Timestamp actual en milisegundos
- **Window Start**: Inicio de la ventana de tiempo (1 minuto)
- **Rate Limit Key**: Combinación de IP y Session ID

### 2. Headers de Rate Limiting
Todas las peticiones HTTP ahora incluyen el header `x-ratelimit-info` con la información necesaria:

```javascript
{
  "ClientIP": "192.168.1.123",
  "SessionId": "session_1234567890_abc123",
  "UserAgent": "Mozilla/5.0...",
  "Timestamp": 1234567890123,
  "RequestCount": 1,
  "WindowStart": 1234567890000,
  "RateLimitKey": "192.168.1.123_session_1234567890_abc123",
  "ClientFingerprint": "abc123def456"
}
```

### 3. Manejo de Errores de Rate Limit
- **Detección automática**: El sistema detecta respuestas HTTP 429
- **Mensajes informativos**: Muestra al usuario cuándo puede intentar nuevamente
- **Deshabilitación temporal**: Los botones se deshabilitan durante el período de espera
- **Retry logic**: Información clara sobre cuándo reintentar

### 4. Indicador Visual de Rate Limit
- **Indicador en tiempo real**: Muestra requests restantes y tiempo de reset
- **Colores dinámicos**: Verde (normal), amarillo (advertencia), rojo (crítico)
- **Animación**: Efecto de pulso cuando está en estado crítico
- **Posición fija**: Visible en la esquina superior derecha

### 5. Funciones Principales

#### `fetchWithRateLimit(url, options)`
Función wrapper que reemplaza todas las llamadas `fetch()` para incluir automáticamente:
- Headers de rate limiting
- Manejo de errores 429
- Actualización del indicador visual

#### `createRateLimitInfo()`
Genera un objeto RateLimitInfo con toda la información necesaria para el middleware.

#### `updateRateLimitInfo(response)`
Extrae información de rate limiting de las respuestas del servidor y actualiza la UI.

#### `showRateLimitError(errorData, retryAfter)`
Maneja errores de rate limit mostrando mensajes informativos y deshabilitando botones.

## Endpoints Actualizados

Todos los endpoints de la API ahora usan `fetchWithRateLimit()`:

- `GET /api/sucursales` - Cargar sucursales
- `GET /api/zonas` - Cargar todas las zonas
- `GET /api/zonas/{id}` - Cargar zonas de una sucursal
- `POST /api/guardar-zona` - Guardar nueva zona
- `POST /api/consultar-cobertura` - Consultar cobertura de dirección
- `DELETE /api/eliminar-zona` - Eliminar zona

## Compatibilidad con el Backend

El frontend es completamente compatible con el middleware de rate limiting del backend:

1. **Header x-ratelimit-info**: Se envía en todas las peticiones
2. **Formato JSON**: Compatible con `JsonConvert.DeserializeObject<RateLimitInfo>()`
3. **Campos requeridos**: Todos los campos marcados como `[Required]` están presentes
4. **Manejo de errores**: Procesa correctamente respuestas 429 con headers de retry

## Pruebas

El sistema incluye una función de prueba (`testRateLimiting()`) que se ejecuta al inicializar la aplicación y verifica:

- Generación correcta de RateLimitInfo
- Serialización/deserialización del header
- Validez de todos los campos requeridos

## Configuración

No se requiere configuración adicional. El sistema se inicializa automáticamente al cargar la página y funciona de forma transparente.

## Logs y Debugging

El sistema genera logs detallados en la consola del navegador para facilitar el debugging:

- Inicialización del sistema
- Información de rate limiting en cada petición
- Errores y manejo de rate limits
- Pruebas del sistema

## Consideraciones de Producción

Para un entorno de producción, se recomienda:

1. **IP Real**: Implementar obtención de IP real del cliente desde el servidor
2. **Persistencia**: Considerar persistir el Session ID en localStorage
3. **Configuración**: Hacer configurable el tiempo de ventana y límites
4. **Monitoreo**: Implementar métricas de rate limiting para análisis
