# Sistema de Zonas de Cobertura - Delivery

Sistema web para definir y gestionar zonas de cobertura de delivery por sucursal, permitiendo dibujar áreas en un mapa interactivo y consultar si direcciones específicas están dentro de las zonas de cobertura.

## Características

- 🗺️ **Mapa Interactivo**: Interfaz web con mapa usando Leaflet para visualizar y dibujar zonas
- 🏪 **Gestión de Sucursales**: CRUD completo para sucursales con coordenadas
- 📍 **Zonas de Cobertura**: Dibujo de polígonos en el mapa para definir áreas de delivery
- 🔍 **Consulta de Direcciones**: Verificación automática si una dirección está en zona de cobertura
- 🏠 **Gestión de Calles**: Definición de rangos de alturas por calle dentro de cada zona
- 📊 **Base de Datos**: Almacenamiento estructurado en SQLite con matriz de cobertura

## Tecnologías Utilizadas

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Mapas**: Leaflet.js con OpenStreetMap
- **Base de Datos**: SQLite
- **Geocodificación**: OpenStreetMap Nominatim API

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

3. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

4. **Acceder a la aplicación**
   - Abrir navegador web
   - Ir a `http://localhost:5000`

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
└── zonas_cobertura.db   # Base de datos SQLite (se crea automáticamente)
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
- `GET /api/sucursales` - Obtener todas las sucursales
- `POST /api/sucursales` - Crear nueva sucursal

### Zonas de Cobertura
- `GET /api/zonas` - Obtener todas las zonas
- `POST /api/zonas` - Crear nueva zona

### Geocodificación
- `POST /api/geocodificar` - Geocodificar dirección
- `POST /api/consultar-cobertura` - Consultar si dirección está en zona

### Calles
- `GET /api/obtener-calles-zona` - Obtener calles de una zona
- `POST /api/guardar-calles-zona` - Guardar calles de una zona

## Base de Datos

### Tablas

#### `sucursales`
- `id` (INTEGER, PRIMARY KEY)
- `nombre` (TEXT)
- `direccion` (TEXT)
- `latitud` (REAL)
- `longitud` (REAL)
- `activa` (BOOLEAN)

#### `zonas_cobertura`
- `id` (INTEGER, PRIMARY KEY)
- `sucursal_id` (INTEGER, FOREIGN KEY)
- `nombre_zona` (TEXT)
- `poligono_coordenadas` (TEXT, JSON)
- `fecha_creacion` (TIMESTAMP)
- `activa` (BOOLEAN)

#### `calles_cobertura`
- `id` (INTEGER, PRIMARY KEY)
- `zona_id` (INTEGER, FOREIGN KEY)
- `nombre_calle` (TEXT)
- `altura_desde` (INTEGER)
- `altura_hasta` (INTEGER)

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
- **Base de Datos**: SQLite con relaciones bien definidas

### Seguridad
- **Validación de Entrada**: Validación de datos en frontend y backend
- **CORS**: Configurado para desarrollo
- **Sanitización**: Limpieza de datos de entrada

## Limitaciones y Mejoras Futuras

### Limitaciones Actuales
- Geocodificación limitada a OpenStreetMap
- No hay autenticación de usuarios
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
