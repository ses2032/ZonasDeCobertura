# Sistema de Zonas de Cobertura - Delivery

Sistema web para definir y gestionar zonas de cobertura de delivery por sucursal, permitiendo dibujar áreas en un mapa interactivo y consultar si direcciones específicas están dentro de las zonas de cobertura.

## Características

- 🗺️ **Mapa Interactivo**: Interfaz web con mapa usando Leaflet para visualizar y dibujar zonas
- 🏪 **Gestión de Sucursales**: CRUD completo para sucursales con coordenadas
- 📍 **Zonas de Cobertura**: Dibujo de polígonos en el mapa para definir áreas de delivery
- 🔍 **Consulta de Direcciones**: Verificación automática si una dirección está en zona de cobertura
- 🏠 **Gestión de Calles**: Definición de rangos de alturas por calle dentro de cada zona
- 🔗 **API Externa**: Integración con API externa para gestión de datos
- 🔐 **Autenticación OAuth**: Sistema de autenticación con Google OAuth 2.0

## Tecnologías Utilizadas

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Mapas**: Leaflet.js con OpenStreetMap
- **API Externa**: Integración con sistema de sucursales
- **Geocodificación**: OpenStreetMap Nominatim API
- **Autenticación**: Google OAuth 2.0 con Authlib

## Estructura del Proyecto

```
ZonasDeCobertura/
├── auth/                                          # Paquete de autenticación OAuth
│   ├── __init__.py                               # Exports del paquete
│   ├── auth.py                                   # Módulo principal de autenticación
│   ├── test_auth.py                              # Pruebas de autenticación
│   ├── client_secret_*.json                      # Credenciales de Google OAuth
│   ├── CONFIGURACION_AUTENTICACION.md            # Guía de configuración
│   ├── IMPLEMENTACION_AUTENTICACION_RESUMEN.md   # Resumen de implementación
│   └── README.md                                 # Documentación del paquete
├── static/                                       # Archivos estáticos (CSS, JS)
├── templates/                                    # Plantillas HTML
├── app.py                                        # Aplicación principal Flask
├── config.py                                     # Configuración de la aplicación
├── api_service.py                                # Servicio para API externa
├── requirements.txt                              # Dependencias de Python
└── README.md                                     # Este archivo
```

## Instalación

### Requisitos Previos

- Python 3.7 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   git clone <url-del-repositorio>
   cd ZonasDeCobertura
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar autenticación OAuth** (Opcional)
   - Ver [auth/CONFIGURACION_AUTENTICACION.md](auth/CONFIGURACION_AUTENTICACION.md) para configuración detallada
   - Configurar variables de entorno para Google OAuth
   - Sin configuración OAuth, la aplicación funcionará en modo desarrollo

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Acceder a la aplicación**
   - Abrir navegador web
   - Ir a `http://localhost:5000`
   - Si está configurado OAuth, hacer login con Google

## Estructura del Proyecto

```
ZonasDeCobertura/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias de Python
├── README.md             # Documentación
├── templates/
│   └── index.html        # Página principal con mapa
├── static/
│   └── app.js           # JavaScript del frontend
└── api_service.py       # Servicio para comunicación con API externa
```

## Uso del Sistema

### 1. Crear Sucursales

1. Hacer clic en "Nueva Sucursal"
2. Completar:
   - Nombre de la sucursal
   - Dirección
   - Coordenadas (latitud y longitud)
3. Guardar

### 2. Definir Zonas de Cobertura

1. Seleccionar una sucursal de la lista
2. Hacer clic en "Dibujar Zona"
3. Dibujar un polígono en el mapa
4. Completar:
   - Sucursal (se pre-selecciona)
   - Nombre de la zona
5. Guardar

### 3. Gestionar Calles de la Zona

1. Hacer clic en "Editar Calles" en una zona
2. Definir:
   - Nombre de la calle
   - Altura desde
   - Altura hasta
3. Guardar cambios

### 4. Consultar Direcciones

1. Ingresar una dirección en el campo de consulta
2. Hacer clic en buscar o presionar Enter
3. Ver resultado:
   - ✅ En zona de cobertura (con detalles de zonas)
   - ❌ Fuera de zona de cobertura

## API Endpoints

### Sucursales
- `GET /api/sucursales` - Obtener todas las sucursales desde API externa

### Zonas de Cobertura
- `GET /api/zonas/{sucursal_id}` - Obtener zonas de una sucursal desde API externa
- `POST /api/guardar-zona` - Guardar zona en API externa
- `DELETE /api/eliminar-zona` - Eliminar zona de API externa

### Geocodificación
- `POST /api/geocodificar` - Geocodificar dirección

## API Externa

El sistema se integra con una API externa que proporciona:

### Endpoints de la API Externa
- `GET /internalapi/SubsidiaryList/1` - Lista de sucursales
- `GET /internalapi/GetZonasCobertura/{sucursalId}` - Zonas de cobertura por sucursal
- `POST /internalapi/GuardarZonaCobertura` - Guardar nueva zona
- `DELETE /internalapi/EliminarZonaCobertura/{sucursalId}/{nombreZona}` - Eliminar zona

### Configuración
- **Base URL**: `http://localhost:5064`
- **Token**: `070CE54A-CF38-4328-90AC-584A1FB3549F`
- **Autenticación**: Bearer Token

## Configuración

### Cambiar Ubicación por Defecto

Para cambiar la ubicación inicial del mapa, editar en `static/app.js`:

```javascript
// Línea 3: Cambiar coordenadas y zoom
map = L.map('map').setView([-34.6037, -58.3816], 12);
// -34.6037, -58.3816 = Buenos Aires, Argentina
```

### Configurar Geocodificación

El sistema usa OpenStreetMap Nominatim por defecto. Para cambiar el proveedor, editar en `app.py`:

```python
# Línea 89: Cambiar geocodificador
geolocator = Nominatim(user_agent="zonas_cobertura_app")
```

## Características Técnicas

### Frontend
- **Responsive Design**: Compatible con dispositivos móviles
- **Mapas Interactivos**: Zoom, pan, dibujo de polígonos
- **Interfaz Moderna**: Bootstrap 5 con gradientes y animaciones
- **Validación**: Validación de formularios en tiempo real

### Backend
- **API RESTful**: Endpoints bien estructurados
- **Manejo de Errores**: Respuestas de error consistentes
- **Geocodificación**: Integración con servicios de geocodificación
- **API Externa**: Integración robusta con sistema de sucursales

### Seguridad
- **Validación de Entrada**: Validación de datos en frontend y backend
- **CORS**: Configurado para desarrollo
- **Sanitización**: Limpieza de datos de entrada

## Limitaciones y Mejoras Futuras

### Limitaciones Actuales
- Geocodificación limitada a OpenStreetMap
- Dependencia de API externa para datos
- Procesamiento de calles simulado (requiere implementación real)

### Mejoras Sugeridas
- [ ] Autenticación y autorización de usuarios
- [ ] Integración con APIs de geocodificación comerciales
- [ ] Procesamiento real de calles desde polígonos
- [ ] Exportación de datos a Excel/CSV
- [ ] Historial de cambios en zonas
- [ ] Notificaciones en tiempo real
- [ ] API para integración con otros sistemas

## Soporte

Para soporte técnico o reportar problemas:
1. Revisar la documentación
2. Verificar logs de la aplicación
3. Comprobar conectividad a internet (para geocodificación)
4. Verificar permisos de escritura en el directorio del proyecto

## Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.
