# Documentación de API - Sistema de Zonas de Cobertura

## Descripción General

Esta documentación describe los endpoints de la API .NET Core que deben ser implementados para el sistema de zonas de cobertura de delivery. La API sigue los lineamientos del endpoint `SubsidiaryList` existente.

## Configuración Base

- **Base URL**: `http://localhost:5064/internalapi`
- **Autenticación**: Bearer Token
- **Token por defecto**: `070CE54A-CF38-4328-90AC-584A1FB3549F`
- **Content-Type**: `application/json`
- **Accept**: `application/json`

## Endpoints Requeridos

### 1. Obtener Zonas de Cobertura por Sucursal

**Endpoint**: `GET /internalapi/ZonasDeCobertura/{sucursalId}`

**Descripción**: Obtiene todas las zonas de cobertura para una sucursal específica.

**Parámetros**:
- `sucursalId` (int): ID de la sucursal

**Headers**:
```
Authorization: Bearer 070CE54A-CF38-4328-90AC-584A1FB3549F
Accept: application/json
```

**Respuesta Exitosa (200 OK)**:
```json
[
    {
        "zonaId": 1,
        "sucursalId": 1,
        "nombreZona": "Zona Centro",
        "poligonoCoordenadas": [
            {
                "latitud": -38.7163706,
                "longitud": -62.2618418
            },
            {
                "latitud": -38.7200000,
                "longitud": -62.2600000
            },
            {
                "latitud": -38.7150000,
                "longitud": -62.2650000
            }
        ],
        "fechaCreacion": "2024-01-15T10:30:00Z",
        "activa": true,
        "calles": [
            {
                "calleId": 1,
                "nombreCalle": "LAMADRID",
                "alturaDesde": 100,
                "alturaHasta": 500
            },
            {
                "calleId": 2,
                "nombreCalle": "SAN MARTIN",
                "alturaDesde": 200,
                "alturaHasta": 800
            }
        ]
    }
]
```

**Respuesta de Error (404 Not Found)**:
```json
{
    "error": "No se encontraron zonas de cobertura para la sucursal especificada",
    "sucursalId": 999
}
```

**Respuesta de Error (500 Internal Server Error)**:
```json
{
    "error": "Error interno del servidor",
    "message": "Detalles del error..."
}
```

### 2. Guardar Zona de Cobertura

**Endpoint**: `POST /internalapi/GuardarZonaCobertura`

**Descripción**: Guarda una nueva zona de cobertura para una sucursal.

**Headers**:
```
Authorization: Bearer 070CE54A-CF38-4328-90AC-584A1FB3549F
Content-Type: application/json
Accept: application/json
```

**Cuerpo de la Petición**:
```json
{
    "sucursalId": 1,
    "nombreZona": "Zona Norte",
    "poligonoCoordenadas": [
        {
            "latitud": -38.7163706,
            "longitud": -62.2618418
        },
        {
            "latitud": -38.7200000,
            "longitud": -62.2600000
        },
        {
            "latitud": -38.7150000,
            "longitud": -62.2650000
        }
    ],
    "activa": true,
    "calles": [
        {
            "nombreCalle": "LAMADRID",
            "alturaDesde": 100,
            "alturaHasta": 500
        },
        {
            "nombreCalle": "SAN MARTIN",
            "alturaDesde": 200,
            "alturaHasta": 800
        }
    ]
}
```

**Respuesta Exitosa (201 Created)**:
```json
{
    "zonaId": 123,
    "message": "Zona de cobertura guardada exitosamente",
    "fechaCreacion": "2024-01-15T10:30:00Z"
}
```

**Respuesta de Error (400 Bad Request)**:
```json
{
    "error": "Datos de entrada inválidos",
    "details": [
        {
            "field": "sucursalId",
            "message": "El ID de sucursal es requerido"
        },
        {
            "field": "nombreZona",
            "message": "El nombre de la zona es requerido"
        }
    ]
}
```

**Respuesta de Error (500 Internal Server Error)**:
```json
{
    "error": "Error interno del servidor",
    "message": "No se pudo guardar la zona de cobertura"
}
```

## Modelos de Datos

### ZonaCobertura
```csharp
public class ZonaCobertura
{
    public int ZonaId { get; set; }
    public int SucursalId { get; set; }
    public string NombreZona { get; set; }
    public List<Coordenada> PoligonoCoordenadas { get; set; }
    public DateTime FechaCreacion { get; set; }
    public bool Activa { get; set; }
    public List<CalleCobertura> Calles { get; set; }
}
```

### Coordenada
```csharp
public class Coordenada
{
    public double Latitud { get; set; }
    public double Longitud { get; set; }
}
```

### CalleCobertura
```csharp
public class CalleCobertura
{
    public int CalleId { get; set; }
    public string NombreCalle { get; set; }
    public int AlturaDesde { get; set; }
    public int AlturaHasta { get; set; }
}
```

### ZonaCoberturaRequest
```csharp
public class ZonaCoberturaRequest
{
    public int SucursalId { get; set; }
    public string NombreZona { get; set; }
    public List<Coordenada> PoligonoCoordenadas { get; set; }
    public bool Activa { get; set; }
    public List<CalleCoberturaRequest> Calles { get; set; }
}
```

### CalleCoberturaRequest
```csharp
public class CalleCoberturaRequest
{
    public string NombreCalle { get; set; }
    public int AlturaDesde { get; set; }
    public int AlturaHasta { get; set; }
}
```

## Implementación Sugerida en .NET Core

### Controller
```csharp
[ApiController]
[Route("internalapi")]
[Authorize] // Implementar autenticación Bearer
public class ZonasCoberturaController : ControllerBase
{
    private readonly IZonasCoberturaService _zonasCoberturaService;

    public ZonasCoberturaController(IZonasCoberturaService zonasCoberturaService)
    {
        _zonasCoberturaService = zonasCoberturaService;
    }

    [HttpGet("ZonasDeCobertura/{sucursalId}")]
    
    public async Task<ActionResult<List<ZonaCobertura>>> GetZonasCobertura(int sucursalId)
    {
        try
        {
            var zonas = await _zonasCoberturaService.GetZonasBySucursalIdAsync(sucursalId);
            return Ok(zonas);
        }
        catch (NotFoundException ex)
        {
            return NotFound(new { error = ex.Message, sucursalId });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = "Error interno del servidor", message = ex.Message });
        }
    }

    [HttpPost("GuardarZonaCobertura")]
    public async Task<ActionResult<object>> GuardarZonaCobertura([FromBody] ZonaCoberturaRequest request)
    {
        try
        {
            if (!ModelState.IsValid)
            {
                var errors = ModelState
                    .Where(x => x.Value.Errors.Count > 0)
                    .Select(x => new { field = x.Key, message = x.Value.Errors.First().ErrorMessage })
                    .ToList();
                
                return BadRequest(new { error = "Datos de entrada inválidos", details = errors });
            }

            var zonaId = await _zonasCoberturaService.GuardarZonaCoberturaAsync(request);
            
            return CreatedAtAction(nameof(GetZonasCobertura), 
                new { sucursalId = request.SucursalId }, 
                new { zonaId, message = "Zona de cobertura guardada exitosamente", fechaCreacion = DateTime.UtcNow });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { error = "Error interno del servidor", message = ex.Message });
        }
    }
}
```

### Service Interface
```csharp
public interface IZonasCoberturaService
{
    Task<List<ZonaCobertura>> GetZonasBySucursalIdAsync(int sucursalId);
    Task<int> GuardarZonaCoberturaAsync(ZonaCoberturaRequest request);
}
```

## Configuración de Swagger

Para documentar automáticamente estos endpoints en Swagger, asegúrate de:

1. Configurar Swagger en `Startup.cs` o `Program.cs`
2. Agregar comentarios XML en los métodos del controller
3. Configurar la autenticación Bearer en Swagger

```csharp
services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "Zonas de Cobertura API", Version = "v1" });
    
    // Configurar autenticación Bearer
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\"",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });
    
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            new string[] {}
        }
    });
});
```

## Variables de Entorno

Para hacer la configuración flexible, utiliza variables de entorno:

```csharp
// En appsettings.json o variables de entorno
{
  "ExternalApi": {
    "BaseUrl": "http://localhost:5064",
    "Token": "070CE54A-CF38-4328-90AC-584A1FB3549F",
    "Timeout": 30
  }
}
```

## Notas de Implementación

1. **Validación**: Implementar validación robusta de los datos de entrada
2. **Logging**: Agregar logging detallado para debugging y monitoreo
3. **Manejo de Errores**: Implementar manejo de errores consistente
4. **Performance**: Considerar implementar caché para consultas frecuentes
5. **Seguridad**: Validar el token Bearer y implementar rate limiting si es necesario
6. **Base de Datos**: Asegurar que las transacciones sean atómicas al guardar zonas con calles
