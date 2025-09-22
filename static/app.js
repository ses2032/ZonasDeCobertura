// Variables globales
let map;
let drawnItems;
let drawControl;
let currentSucursal = null;
let currentZona = null;
let isDrawingMode = false;
let sucursales = [];
let zonas = [];
let sucursalMarker = null;
let hasUnsavedChanges = false;
let originalZonas = [];

// Variables de autenticación
let isAuthenticated = false;
let currentUser = null;
let authCookie = null;

// Variables para rate limiting
let rateLimitInfo = null;
let sessionId = generateSessionId();
let clientFingerprint = generateClientFingerprint();

// Función para normalizar coordenadas y asegurar consistencia
function normalizeCoordinates(coords) {
    if (!Array.isArray(coords)) {
        return coords;
    }
    
    return coords.map(coord => {
        if (typeof coord === 'object' && coord !== null) {
            // Normalizar a 6 decimales para mantener precisión pero evitar diferencias mínimas
            return {
                latitud: parseFloat(coord.latitud || coord.lat).toFixed(6),
                longitud: parseFloat(coord.longitud || coord.lng).toFixed(6)
            };
        }
        return coord;
    });
}

// =============================================================================
// FUNCIONES DE RATE LIMITING
// =============================================================================

// Generar un ID de sesión único
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Generar un fingerprint del cliente
function generateClientFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Client fingerprint', 2, 2);
    
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset(),
        canvas.toDataURL()
    ].join('|');
    
    // Crear hash simple del fingerprint
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convertir a 32-bit integer
    }
    return Math.abs(hash).toString(36);
}

// Obtener la IP del cliente (simulada para desarrollo)
function getClientIP() {
    // En un entorno real, esto vendría del servidor
    // Para desarrollo, usamos una IP simulada basada en el fingerprint
    return '192.168.1.' + (Math.abs(clientFingerprint.charCodeAt(0)) % 255);
}

// Crear objeto RateLimitInfo
function createRateLimitInfo() {
    const now = Date.now();
    const windowStart = Math.floor(now / 60000) * 60000; // Ventana de 1 minuto
    
    return {
        ClientIP: getClientIP(),
        SessionId: sessionId,
        UserAgent: navigator.userAgent,
        Timestamp: now,
        RequestCount: 1,
        WindowStart: windowStart,
        RateLimitKey: `${getClientIP()}_${sessionId}`,
        ClientFingerprint: clientFingerprint
    };
}

// Actualizar RateLimitInfo con información de respuesta
function updateRateLimitInfo(response) {
    const limit = response.headers.get('X-RateLimit-Limit');
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const reset = response.headers.get('X-RateLimit-Reset');
    
    if (limit && remaining && reset) {
        rateLimitInfo = {
            ...rateLimitInfo,
            Limit: parseInt(limit),
            Remaining: parseInt(remaining),
            ResetTime: parseInt(reset)
        };
        
        // Actualizar UI con información de rate limit
        updateRateLimitDisplay();
    }
}

// Actualizar la visualización del rate limit en la UI
function updateRateLimitDisplay() {
    if (!rateLimitInfo || !rateLimitInfo.Limit) return;
    
    const remaining = rateLimitInfo.Remaining || 0;
    const limit = rateLimitInfo.Limit;
    const resetTime = rateLimitInfo.ResetTime;
    
    // Crear o actualizar el indicador de rate limit
    let rateLimitIndicator = document.getElementById('rateLimitIndicator');
    if (!rateLimitIndicator) {
        rateLimitIndicator = document.createElement('div');
        rateLimitIndicator.id = 'rateLimitIndicator';
        rateLimitIndicator.className = 'rate-limit-indicator';
        rateLimitIndicator.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(rateLimitIndicator);
    }
    
    const resetDate = new Date(resetTime * 1000);
    const timeUntilReset = Math.max(0, Math.ceil((resetDate - new Date()) / 1000));
    
    rateLimitIndicator.innerHTML = `
        <i class="fas fa-tachometer-alt me-1"></i>
        ${remaining}/${limit} requests
        <br>
        <small>Reset en ${timeUntilReset}s</small>
    `;
    
    // Actualizar clases CSS según el estado
    rateLimitIndicator.classList.remove('high', 'medium', 'low');
    if (remaining > limit * 0.5) {
        rateLimitIndicator.classList.add('high');
    } else if (remaining > limit * 0.2) {
        rateLimitIndicator.classList.add('medium');
    } else {
        rateLimitIndicator.classList.add('low');
    }
}

// Función para hacer peticiones HTTP con rate limiting
async function fetchWithRateLimit(url, options = {}) {
    // Crear RateLimitInfo si no existe
    if (!rateLimitInfo) {
        rateLimitInfo = createRateLimitInfo();
    }
    
    // Agregar headers de rate limiting
    const headers = {
        'Content-Type': 'application/json',
        'x-ratelimit-info': JSON.stringify(rateLimitInfo),
        ...options.headers
    };
    
    const requestOptions = {
        ...options,
        headers,
        credentials: 'include'  // Incluir cookies de sesión
    };
    
    try {
        const response = await fetch(url, requestOptions);
        
        // Actualizar información de rate limit desde la respuesta
        updateRateLimitInfo(response);
        
        // Manejar errores de rate limit
        if (response.status === 429) {
            const errorData = await response.json();
            const retryAfter = response.headers.get('Retry-After');
            
            showRateLimitError(errorData, retryAfter);
            throw new Error(`Rate limit exceeded: ${errorData.message}`);
        }
        
        return response;
    } catch (error) {
        if (error.message.includes('Rate limit exceeded')) {
            throw error;
        }
        throw new Error(`Network error: ${error.message}`);
    }
}

// Mostrar error de rate limit
function showRateLimitError(errorData, retryAfter) {
    const retrySeconds = parseInt(retryAfter) || 60;
    const retryDate = new Date(Date.now() + retrySeconds * 1000);
    
    const errorMessage = `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Límite de solicitudes excedido</strong><br>
            ${errorData.message}<br>
            <small>Puede intentar nuevamente en ${retrySeconds} segundos (${retryDate.toLocaleTimeString()})</small>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Mostrar alerta
    showAlert(`Límite de solicitudes excedido. Intente nuevamente en ${retrySeconds} segundos.`, 'warning');
    
    // Deshabilitar botones temporalmente
    disableButtonsTemporarily(retrySeconds);
}

// Deshabilitar botones temporalmente
function disableButtonsTemporarily(seconds) {
    const buttons = document.querySelectorAll('button:not(.btn-close)');
    const originalTexts = new Map();
    
    buttons.forEach(button => {
        originalTexts.set(button, button.innerHTML);
        button.disabled = true;
        button.innerHTML = `<i class="fas fa-clock me-1"></i>Esperando ${seconds}s`;
    });
    
    // Rehabilitar botones después del tiempo de espera
    setTimeout(() => {
        buttons.forEach(button => {
            button.disabled = false;
            const originalText = originalTexts.get(button);
            if (originalText) {
                button.innerHTML = originalText;
            }
        });
    }, seconds * 1000);
}

// Función para probar el sistema de rate limiting
function testRateLimiting() {
    console.log('=== PRUEBA DEL SISTEMA DE RATE LIMITING ===');
    console.log('RateLimitInfo actual:', rateLimitInfo);
    console.log('Session ID:', sessionId);
    console.log('Client Fingerprint:', clientFingerprint);
    console.log('Client IP:', getClientIP());
    
    // Probar creación de RateLimitInfo
    const testRateLimitInfo = createRateLimitInfo();
    console.log('RateLimitInfo de prueba:', testRateLimitInfo);
    
    // Verificar que el header se genera correctamente
    const headerValue = JSON.stringify(testRateLimitInfo);
    console.log('Header x-ratelimit-info:', headerValue);
    
    // Verificar que se puede parsear correctamente
    try {
        const parsed = JSON.parse(headerValue);
        console.log('Header parseado correctamente:', parsed);
    } catch (error) {
        console.error('Error parseando header:', error);
    }
    
    console.log('=== FIN DE PRUEBA ===');
}

// Inicialización del mapa
function initMap() {
    // Crear mapa centrado en Buenos Aires (puedes cambiar las coordenadas)
    map = L.map('map').setView([-34.6037, -58.3816], 12);
    
    // Agregar capa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Inicializar capa para elementos dibujados
    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    
    // Configurar controles de dibujo
    drawControl = new L.Control.Draw({
        position: 'topright',
        draw: {
            polygon: {
                allowIntersection: false,
                showArea: true,
                drawError: {
                    color: '#e1e100',
                    message: '<strong>Error:</strong> El polígono no puede intersectarse consigo mismo!'
                },
                shapeOptions: {
                    color: '#667eea',
                    fillColor: '#667eea',
                    fillOpacity: 0.2
                }
            },
            polyline: false,
            rectangle: false,
            circle: false,
            marker: false,
            circlemarker: false
        },
        edit: {
            featureGroup: drawnItems,
            remove: true
        }
    });
    
    map.addControl(drawControl);
    
    // Eventos de dibujo
    map.on(L.Draw.Event.CREATED, function(event) {
        const layer = event.layer;
        drawnItems.addLayer(layer);
        
        if (isDrawingMode) {
            showZonaModal(layer);
        } else {
            // Si se crea un polígono fuera del modo dibujo, agregarlo como zona temporal
            if (currentSucursal) {
                const coordenadasRaw = layer.getLatLngs()[0].map(latlng => ({
                    latitud: latlng.lat,
                    longitud: latlng.lng
                }));
                
                const coordenadas = normalizeCoordinates(coordenadasRaw);
                
                console.log('=== COORDENADAS ZONA TEMPORAL ===');
                console.log('Coordenadas originales:', coordenadasRaw);
                console.log('Coordenadas normalizadas:', coordenadas);
                console.log('Primera coordenada:', coordenadas[0]);
                console.log('Última coordenada:', coordenadas[coordenadas.length - 1]);
                
                const zonaTemporal = {
                    id: null, // Zona temporal sin ID
                    sucursal_id: currentSucursal.id,
                    nombre_zona: `Zona temporal ${Date.now()}`, // Nombre temporal
                    poligono_coordenadas: coordenadas,
                    activa: true,
                    sucursal_nombre: currentSucursal.nombre,
                    temporal: true // Marcar como temporal
                };
                
                // Agregar la zona temporal al array local
                zonas.push(zonaTemporal);
                
                // Marcar que hay cambios sin guardar
                markAsChanged(currentSucursal.id);
                
                // Actualizar la visualización
                renderZonas();
            }
        }
    });
    
    map.on(L.Draw.Event.EDITED, function(event) {
        console.log('Polígono editado');
        // Actualizar las coordenadas en el array local cuando se edita un polígono
        if (currentSucursal) {
            const layers = event.layers;
            let hasChanges = false;
            
            layers.eachLayer(function(layer) {
                if (layer.options && layer.options.isZona && layer.options.zonaId) {
                    // Encontrar la zona en el array local y actualizar sus coordenadas
                    const zona = zonas.find(z => z.id === layer.options.zonaId);
                    if (zona) {
                        const coordenadasRaw = layer.getLatLngs()[0].map(latlng => ({
                            latitud: latlng.lat,
                            longitud: latlng.lng
                        }));
                        
                        const coordenadas = normalizeCoordinates(coordenadasRaw);
                        
                        console.log('=== COORDENADAS EXTRAÍDAS AL EDITAR ===');
                        console.log('Zona editada:', zona.nombre_zona);
                        console.log('Coordenadas originales:', coordenadasRaw);
                        console.log('Coordenadas normalizadas:', coordenadas);
                        console.log('Primera coordenada:', coordenadas[0]);
                        console.log('Última coordenada:', coordenadas[coordenadas.length - 1]);
                        
                        // Verificar si las coordenadas realmente cambiaron
                        const coordenadasAnteriores = zona.poligono_coordenadas;
                        const coordenadasCambiaron = JSON.stringify(coordenadas) !== JSON.stringify(coordenadasAnteriores);
                        
                        if (coordenadasCambiaron) {
                            console.log('Coordenadas de zona modificadas:', zona.nombre_zona);
                            console.log('Coordenadas anteriores:', coordenadasAnteriores);
                            console.log('Coordenadas nuevas:', coordenadas);
                            
                            zona.poligono_coordenadas = coordenadas;
                            hasChanges = true;
                        }
                    }
                }
            });
            
            // Marcar que hay cambios sin guardar solo si realmente hubo cambios
            if (hasChanges) {
                markAsChanged(currentSucursal.id);
            }
        }
    });
    
    map.on(L.Draw.Event.DELETED, function(event) {
        console.log('Polígono eliminado');
        // Marcar que hay cambios sin guardar cuando se elimina un polígono
        if (currentSucursal) {
            markAsChanged(currentSucursal.id);
        }
    });
    
    // Cargar datos iniciales
    loadSucursales();
    loadZonas();
}

// Cargar sucursales
async function loadSucursales() {
    try {
        console.log('Iniciando carga de sucursales...');
        const response = await apiCall('/api/sucursales');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        sucursales = await response.json();
        console.log('Sucursales cargadas exitosamente:', sucursales);
        renderSucursales();
    } catch (error) {
        console.error('Error cargando sucursales:', error);
        if (error.message.includes('Rate limit exceeded')) {
            // El error de rate limit ya se maneja en fetchWithRateLimit
            return;
        }
        if (error.message.includes('Sesión expirada') || error.message.includes('Autenticación requerida')) {
            console.log('Error de autenticación al cargar sucursales');
            return; // No mostrar alerta, ya se maneja en apiCall
        }
        showAlert('Error al cargar sucursales. Verifique su conexión e intente nuevamente.', 'danger');
    }
}

// Renderizar sucursales en la lista
function renderSucursales() {
    const container = document.getElementById('listaSucursales');
    
    if (sucursales.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay sucursales registradas</p>';
        return;
    }
    
    container.innerHTML = sucursales.map(sucursal => `
        <div class="sucursal-item" onclick="selectSucursal(${sucursal.id})" data-id="${sucursal.id}">
            <h6>${sucursal.nombre}</h6>
            <small class="text-muted">${sucursal.direccion}</small>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); showSucursalOnMap(${sucursal.id})" title="Centrar en mapa">
                    <i class="fas fa-map-marker-alt"></i>
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="event.stopPropagation(); createZoneForSucursal(${sucursal.id})" title="Crear zona">
                    <i class="fas fa-plus"></i>
                </button>
                <button class="btn btn-save-changes" onclick="event.stopPropagation(); saveZonasChanges(${sucursal.id})" title="Guardar cambios" id="btnSaveChanges_${sucursal.id}">
                    <i class="fas fa-save"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Cargar zonas de cobertura
async function loadZonas() {
    try {
        console.log('Iniciando carga de zonas...');
        const response = await apiCall('/api/zonas');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        zonas = await response.json();
        console.log('Zonas cargadas exitosamente:', zonas);
        renderZonas();
        renderZonasOnMap();
    } catch (error) {
        console.error('Error cargando zonas:', error);
        if (error.message.includes('Rate limit exceeded')) {
            // El error de rate limit ya se maneja en fetchWithRateLimit
            return;
        }
        if (error.message.includes('Sesión expirada') || error.message.includes('Autenticación requerida')) {
            console.log('Error de autenticación al cargar zonas');
            return; // No mostrar alerta, ya se maneja en apiCall
        }
        showAlert('Error al cargar zonas. Verifique su conexión e intente nuevamente.', 'danger');
    }
}

// Cargar zonas de cobertura para una sucursal específica
async function loadZonasSucursal(sucursalId) {
    try {
        // Mostrar indicador de carga
        const listaZonas = document.getElementById('listaZonas');
        listaZonas.innerHTML = `
            <div class="loading">
                <div class="spinner-border spinner-border-custom" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2">Cargando zonas de la sucursal...</p>
            </div>
        `;
        
        const response = await fetchWithRateLimit(`/api/zonas/${sucursalId}`);
        if (response.ok) {
            const zonasSucursal = await response.json();
            console.log('Zonas cargadas de la API:', zonasSucursal);
            
            // Actualizar la lista de zonas con las de la sucursal seleccionada
            zonas = zonasSucursal;
            // Guardar el estado original para detectar cambios
            originalZonas = JSON.parse(JSON.stringify(zonas));
            hasUnsavedChanges = false;
            updateSaveButtonVisibility(sucursalId);
            renderZonas();
            renderZonasOnMap();
            
            // Mostrar mensaje si no hay zonas
            if (zonas.length === 0) {
                showAlert('Esta sucursal no tiene zonas de cobertura definidas', 'info');
            }
        } else {
            console.warn(`No se encontraron zonas para la sucursal ${sucursalId}`);
            zonas = [];
            renderZonas();
            renderZonasOnMap();
            showAlert('No se encontraron zonas de cobertura para esta sucursal', 'warning');
        }
    } catch (error) {
        console.error('Error cargando zonas de sucursal:', error);
        if (error.message.includes('Rate limit exceeded')) {
            // El error de rate limit ya se maneja en fetchWithRateLimit
            return;
        }
        showAlert('Error al cargar zonas de la sucursal', 'danger');
        
        // Mostrar mensaje de error en la lista
        const listaZonas = document.getElementById('listaZonas');
        listaZonas.innerHTML = `
            <div class="alert alert-danger alert-custom">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error al cargar las zonas de cobertura
            </div>
        `;
    }
}

// Renderizar zonas en la lista
function renderZonas() {
    const container = document.getElementById('listaZonas');
    console.log('renderZonas llamado, zonas totales:', zonas.length);
    
    // Filtrar zonas que no están marcadas como eliminadas
    const zonasVisibles = zonas.filter(zona => !zona.eliminada);
    console.log('zonas visibles:', zonasVisibles.length);
    
    if (zonasVisibles.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay zonas de cobertura</p>';
        return;
    }
    
    container.innerHTML = zonasVisibles.map(zona => {
        const zonaId = zona.id || zona.zonaId;
        const nombreZona = zona.nombre_zona || zona.nombreZona;
        const sucursalNombre = zona.sucursal_nombre || 
                             (currentSucursal ? currentSucursal.nombre : 'Sucursal');
        
        return `
            <div class="zona-item">
                <h6>${nombreZona}</h6>
                <small class="text-muted">Sucursal: ${sucursalNombre}</small>
                <div class="mt-2">
                    <button class="btn btn-sm btn-outline-info" onclick="showZonaOnMap(${zonaId})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteZona(${zonaId})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Renderizar zonas en el mapa
function renderZonasOnMap() {
    console.log('renderZonasOnMap llamado, zonas totales:', zonas.length);
    
    // Verificar que el mapa esté inicializado
    if (!map) {
        console.log('Mapa no inicializado, saltando renderizado de zonas');
        return;
    }
    
    // Limpiar zonas existentes
    clearExistingPolygons();
    
    // Filtrar zonas que no están marcadas como eliminadas
    const zonasVisibles = zonas.filter(zona => !zona.eliminada);
    console.log('zonas visibles para renderizar en mapa:', zonasVisibles.length);
    
    zonasVisibles.forEach(zona => {
        try {
            console.log('Renderizando zona:', zona);
            let coordenadas;
            
            // Manejar diferentes formatos de coordenadas
            if (typeof zona.poligono_coordenadas === 'string') {
                coordenadas = JSON.parse(zona.poligono_coordenadas);
            } else {
                coordenadas = zona.poligono_coordenadas;
            }
            
            console.log('Coordenadas parseadas para zona:', zona.nombre_zona || zona.nombreZona, coordenadas);
            
            // Normalizar coordenadas recibidas de la API
            const coordenadasNormalizadas = normalizeCoordinates(coordenadas);
            console.log('Coordenadas normalizadas:', coordenadasNormalizadas);
            
            // Validar que las coordenadas existan
            if (!coordenadas || !Array.isArray(coordenadas) || coordenadas.length < 3) {
                console.warn('Zona con coordenadas inválidas:', zona);
                return;
            }
            
            console.log('Coordenadas válidas para zona:', zona.nombre_zona || zona.nombreZona);
            
            // Convertir coordenadas normalizadas al formato esperado por Leaflet
            const latLngs = coordenadasNormalizadas.map(coord => {
                if (Array.isArray(coord)) {
                    // Formato [lat, lng]
                    return [coord[0], coord[1]];
                } else if (coord.latitud !== undefined && coord.longitud !== undefined) {
                    // Formato {latitud, longitud}
                    return [coord.latitud, coord.longitud];
                } else if (coord.lat !== undefined && coord.lng !== undefined) {
                    // Formato {lat, lng}
                    return [coord.lat, coord.lng];
                } else {
                    console.error('Formato de coordenada no reconocido:', coord);
                    return [0, 0]; // Coordenada por defecto en caso de error
                }
            });
            
            // Usar el mismo estilo que cuando se crean los polígonos
            const polygon = L.polygon(latLngs, {
                color: '#667eea',           // Mismo color que en drawControl
                fillColor: '#667eea',       // Mismo color de relleno
                fillOpacity: 0.2,           // Misma opacidad
                weight: 2,                  // Grosor del borde
                isZona: true,
                zonaId: zona.id || zona.zonaId
            }).addTo(map);
            
            console.log('Polígono agregado al mapa para zona:', zona.nombre_zona || zona.nombreZona);
            
            const sucursalNombre = zona.sucursal_nombre || 
                                 (currentSucursal ? currentSucursal.nombre : 'Sucursal');
            
            polygon.bindPopup(`
                <div class="text-center">
                    <strong>${zona.nombre_zona || zona.nombreZona}</strong><br>
                    <small class="text-muted">Sucursal: ${sucursalNombre}</small><br>
                    <button class="btn btn-sm btn-danger mt-2" onclick="deleteZona(${zona.id || zona.zonaId})">
                        <i class="fas fa-trash me-1"></i>Eliminar Zona
                    </button>
                </div>
            `);
            
            // Agregar evento de click para mostrar información
            polygon.on('click', function(e) {
                console.log('Zona clickeada:', zona);
            });
            
        } catch (error) {
            console.error('Error renderizando zona:', error, zona);
        }
    });
    
    console.log('Renderizado de zonas en mapa completado');
    
    // Mostrar mensaje si se cargaron zonas
    if (zonas.length > 0) {
        showAlert(`Se cargaron ${zonas.length} zona(s) de cobertura`, 'success');
    }
}

// Seleccionar sucursal
function selectSucursal(sucursalId) {
    console.log('selectSucursal llamado para sucursal:', sucursalId);
    
    // Remover selección anterior
    document.querySelectorAll('.sucursal-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Seleccionar nueva sucursal
    const item = document.querySelector(`[data-id="${sucursalId}"]`);
    if (item) {
        item.classList.add('active');
        currentSucursal = sucursales.find(s => s.id === sucursalId);
        console.log('Sucursal seleccionada:', currentSucursal);
        
        // Limpiar polígonos y marcadores existentes del mapa
        clearExistingPolygons();
        clearSucursalMarker();
        
        // Mostrar marcador de la sucursal seleccionada
        showSucursalMarker(currentSucursal);
        
        // Cargar zonas específicas para esta sucursal
        loadZonasSucursal(sucursalId);
        
        // Centrar el mapa en la sucursal seleccionada
        if (currentSucursal && map) {
            map.setView([currentSucursal.latitud, currentSucursal.longitud], 13);
        }
    }
}

// Mostrar sucursal en el mapa
function showSucursalOnMap(sucursalId) {
    const sucursal = sucursales.find(s => s.id === sucursalId);
    if (sucursal && map) {
        map.setView([sucursal.latitud, sucursal.longitud], 15);
        
        // Agregar marcador temporal
        L.marker([sucursal.latitud, sucursal.longitud])
            .addTo(map)
            .bindPopup(`
                <strong>${sucursal.nombre}</strong><br>
                ${sucursal.direccion}
            `)
            .openPopup();
    }
}

// Mostrar zona en el mapa
function showZonaOnMap(zonaId) {
    const zona = zonas.find(z => (z.id === zonaId) || (z.zonaId === zonaId));
    if (zona) {
        try {
            let coordenadas;
            
            // Manejar diferentes formatos de coordenadas
            if (typeof zona.poligono_coordenadas === 'string') {
                coordenadas = JSON.parse(zona.poligono_coordenadas);
            } else {
                coordenadas = zona.poligono_coordenadas;
            }
            
            console.log('Coordenadas parseadas para mostrar zona:', zona.nombre_zona || zona.nombreZona, coordenadas);
            
            // Normalizar coordenadas recibidas de la API
            const coordenadasNormalizadas = normalizeCoordinates(coordenadas);
            console.log('Coordenadas normalizadas para mostrar:', coordenadasNormalizadas);
            
            // Convertir coordenadas normalizadas al formato esperado por Leaflet
            const latLngs = coordenadasNormalizadas.map(coord => {
                if (Array.isArray(coord)) {
                    // Formato [lat, lng]
                    return [coord[0], coord[1]];
                } else if (coord.latitud !== undefined && coord.longitud !== undefined) {
                    // Formato {latitud, longitud}
                    return [coord.latitud, coord.longitud];
                } else if (coord.lat !== undefined && coord.lng !== undefined) {
                    // Formato {lat, lng}
                    return [coord.lat, coord.lng];
                } else {
                    console.error('Formato de coordenada no reconocido:', coord);
                    return [0, 0]; // Coordenada por defecto en caso de error
                }
            });
            
            const bounds = L.polygon(latLngs).getBounds();
            if (map) {
                map.fitBounds(bounds);
            }
        } catch (error) {
            console.error('Error mostrando zona:', error);
        }
    }
}

// Crear zona para sucursal
function createZoneForSucursal(sucursalId) {
    console.log('createZoneForSucursal llamado para sucursal:', sucursalId);
    currentSucursal = sucursales.find(s => s.id === sucursalId);
    startDrawingZone();
}

// Iniciar modo de dibujo
function startDrawingZone() {
    requireAuth(() => {
        console.log('startDrawingZone llamado, currentSucursal:', currentSucursal);
        
        if (!currentSucursal) {
            showAlert('Por favor seleccione una sucursal primero', 'warning');
            return;
        }
        
        isDrawingMode = true;
        document.getElementById('btnDrawZone').innerHTML = '<i class="fas fa-stop me-2"></i>Cancelar Dibujo';
        document.getElementById('btnDrawZone').onclick = cancelDrawing;
        
        showAlert('Dibuje un polígono en el mapa para definir la zona de cobertura', 'info');
    });
}

// Cancelar dibujo
function cancelDrawing() {
    console.log('cancelDrawing llamado');
    isDrawingMode = false;
    document.getElementById('btnDrawZone').innerHTML = '<i class="fas fa-draw-polygon me-2"></i>Dibujar Zona';
    document.getElementById('btnDrawZone').onclick = startDrawingZone;
    
    // Limpiar elementos dibujados
    drawnItems.clearLayers();
}

// Mostrar modal de zona
function showZonaModal(layer) {
    console.log('showZonaModal llamado, isDrawingMode:', isDrawingMode);
    
    if (!isDrawingMode) return;
    
    currentZona = layer;
    
    // Llenar select de sucursales
    const select = document.getElementById('sucursalZona');
    select.innerHTML = '<option value="">Seleccione una sucursal</option>';
    sucursales.forEach(sucursal => {
        const option = document.createElement('option');
        option.value = sucursal.id;
        option.textContent = sucursal.nombre;
        if (sucursal.id === currentSucursal.id) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalZona'));
    modal.show();
}

// Guardar zona
async function saveZona() {
    console.log('saveZona llamado');
    
    const sucursalId = document.getElementById('sucursalZona').value;
    const nombreZona = document.getElementById('nombreZona').value;
    
    console.log('sucursalId:', sucursalId, 'nombreZona:', nombreZona);
    
    if (!sucursalId || !nombreZona) {
        showAlert('Por favor complete todos los campos', 'warning');
        return;
    }
    
    if (!currentZona) {
        showAlert('No hay polígono dibujado', 'error');
        return;
    }
    
    try {
        const coordenadasRaw = currentZona.getLatLngs()[0].map(latlng => ({
            latitud: latlng.lat,
            longitud: latlng.lng
        }));
        
        const coordenadas = normalizeCoordinates(coordenadasRaw);
        
        console.log('=== COORDENADAS EXTRAÍDAS DEL POLÍGONO ===');
        console.log('Coordenadas originales:', coordenadasRaw);
        console.log('Coordenadas normalizadas:', coordenadas);
        console.log('Número de vértices:', coordenadas.length);
        console.log('Primera coordenada:', coordenadas[0]);
        console.log('Última coordenada:', coordenadas[coordenadas.length - 1]);
        console.log('Tipo de primera coordenada:', typeof coordenadas[0]);
        console.log('Latitud primera coordenada:', coordenadas[0].latitud);
        console.log('Longitud primera coordenada:', coordenadas[0].longitud);
        
        const response = await fetchWithRateLimit('/api/guardar-zona', {
            method: 'POST',
            body: JSON.stringify({
                sucursal_id: parseInt(sucursalId),
                nombre_zona: nombreZona,
                poligono_coordenadas: coordenadas,
                activa: true
            })
        });
        
        console.log('Respuesta de la API:', response);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Resultado de la API:', result);
            
            showAlert('Zona creada exitosamente', 'success');
            bootstrap.Modal.getInstance(document.getElementById('modalZona')).hide();
            
            // Limpiar formulario
            document.getElementById('formZona').reset();
            drawnItems.clearLayers();
            
            // Agregar la zona al array local
            const nuevaZona = {
                id: result.data?.zonaId || result.data?.id || null, // Usar el ID devuelto por la API
                sucursal_id: parseInt(sucursalId),
                nombre_zona: nombreZona,
                poligono_coordenadas: coordenadas,
                activa: true,
                sucursal_nombre: currentSucursal ? currentSucursal.nombre : 'Sucursal'
            };
            
            console.log('Nueva zona agregada al array local:', nuevaZona);
            
            // Agregar la zona al array local
            zonas.push(nuevaZona);
            
            // Marcar que hay cambios sin guardar
            if (currentSucursal) {
                markAsChanged(currentSucursal.id);
            }
            
            // Actualizar la visualización
            renderZonas();
            renderZonasOnMap();
            
            // Salir del modo dibujo
            cancelDrawing();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al crear zona');
        }
    } catch (error) {
        console.error('Error guardando zona:', error);
        if (error.message.includes('Rate limit exceeded')) {
            // El error de rate limit ya se maneja en fetchWithRateLimit
            return;
        }
        showAlert(`Error al guardar la zona: ${error.message}`, 'danger');
    }
}


// Consultar dirección
async function consultarDireccion() {
    requireAuth(async () => {
        const direccion = document.getElementById('direccionConsulta').value.trim();
        
        if (!direccion) {
            showAlert('Por favor ingrese una dirección', 'warning');
            return;
        }
        
        const resultadoContainer = document.getElementById('resultadoConsulta');
        resultadoContainer.innerHTML = `
            <div class="loading">
                <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Consultando...</span>
                </div>
                <span class="ms-2">Consultando dirección...</span>
            </div>
        `;
        
        try {
            const response = await apiCall('/api/consultar-cobertura', {
                method: 'POST',
                body: JSON.stringify({ direccion: direccion })
            });
            
            const resultado = await response.json();
            
            if (response.ok) {
                renderConsultaResultado(resultado);
            } else {
                resultadoContainer.innerHTML = `
                    <div class="alert alert-danger alert-custom">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${resultado.error}
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error consultando dirección:', error);
            if (error.message.includes('Rate limit exceeded')) {
                // El error de rate limit ya se maneja en fetchWithRateLimit
                return;
            }
            resultadoContainer.innerHTML = `
                <div class="alert alert-danger alert-custom">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error al consultar la dirección
                </div>
            `;
        }
    });
}

// Renderizar resultado de consulta
function renderConsultaResultado(resultado) {
    const container = document.getElementById('resultadoConsulta');
    
    if (resultado.en_zona_cobertura) {
        container.innerHTML = `
            <div class="coverage-result">
                <h6><i class="fas fa-check-circle me-2 text-success"></i>En Zona de Cobertura</h6>
                <p><strong>Dirección:</strong> ${resultado.direccion}</p>
                <p><strong>Coordenadas:</strong> ${resultado.coordenadas.latitud.toFixed(6)}, ${resultado.coordenadas.longitud.toFixed(6)}</p>
                <div class="mt-2">
                    <strong>Zonas que cubren esta dirección:</strong>
                    <ul class="mt-1">
                        ${resultado.zonas.map(zona => `
                            <li>${zona.nombre_zona} - ${zona.sucursal_nombre}</li>
                        `).join('')}
                    </ul>
                </div>
                <button class="btn btn-sm btn-primary" onclick="showDireccionOnMap(${resultado.coordenadas.latitud}, ${resultado.coordenadas.longitud})">
                    <i class="fas fa-map-marker-alt me-1"></i>Ver en Mapa
                </button>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="coverage-result no-coverage">
                <h6><i class="fas fa-times-circle me-2 text-danger"></i>Fuera de Zona de Cobertura</h6>
                <p><strong>Dirección:</strong> ${resultado.direccion}</p>
                <p><strong>Coordenadas:</strong> ${resultado.coordenadas.latitud.toFixed(6)}, ${resultado.coordenadas.longitud.toFixed(6)}</p>
                <p class="text-muted">Esta dirección no está cubierta por ninguna zona de delivery.</p>
                <button class="btn btn-sm btn-primary" onclick="showDireccionOnMap(${resultado.coordenadas.latitud}, ${resultado.coordenadas.longitud})">
                    <i class="fas fa-map-marker-alt me-1"></i>Ver en Mapa
                </button>
            </div>
        `;
    }
}

// Mostrar dirección en el mapa
function showDireccionOnMap(lat, lng) {
    if (!map) return;
    
    map.setView([lat, lng], 16);
    
    L.marker([lat, lng])
        .addTo(map)
        .bindPopup('Dirección consultada')
        .openPopup();
}

// Eliminar zona
async function deleteZona(zonaId) {
    const zona = zonas.find(z => (z.id === zonaId) || (z.zonaId === zonaId));
    if (!zona) {
        showAlert('Zona no encontrada', 'error');
        return;
    }
    
    const nombreZona = zona.nombre_zona || zona.nombreZona;
    const confirmDelete = confirm(`¿Está seguro que desea eliminar la zona "${nombreZona}"?`);
    
    if (!confirmDelete) {
        return;
    }
    
    try {
        // Marcar la zona como eliminada (no la eliminamos físicamente hasta guardar)
        zona.eliminada = true;
        
        // Remover el polígono del mapa
        map.eachLayer(layer => {
            if (layer.options && layer.options.isZona && layer.options.zonaId === zonaId) {
                map.removeLayer(layer);
            }
        });
            
            // Marcar que hay cambios sin guardar
            if (currentSucursal) {
                markAsChanged(currentSucursal.id);
            }
        
        // Actualizar la lista de zonas
        renderZonas();
        
        showAlert(`Zona "${nombreZona}" marcada para eliminación`, 'warning');
        
    } catch (error) {
        console.error('Error eliminando zona:', error);
        showAlert('Error al eliminar la zona', 'danger');
    }
}

// Limpiar polígonos existentes del mapa
function clearExistingPolygons() {
    if (map) {
        map.eachLayer(layer => {
            if (layer.options && layer.options.isZona) {
                map.removeLayer(layer);
            }
        });
    }
}

// Limpiar marcador de sucursal
function clearSucursalMarker() {
    if (sucursalMarker && map) {
        map.removeLayer(sucursalMarker);
        sucursalMarker = null;
    }
}

// Mostrar marcador de sucursal
function showSucursalMarker(sucursal) {
    if (!sucursal || !map) return;
    
    // Limpiar marcador anterior si existe
    clearSucursalMarker();
    
    // Crear icono personalizado para la sucursal
    const sucursalIcon = L.divIcon({
        className: 'sucursal-marker',
        html: '<i class="fas fa-store" style="color: #667eea; font-size: 24px;"></i>',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });
    
    // Crear marcador
    sucursalMarker = L.marker([sucursal.latitud, sucursal.longitud], {
        icon: sucursalIcon
    }).addTo(map);
    
    // Agregar popup con información de la sucursal
    sucursalMarker.bindPopup(`
        <div class="text-center">
            <h6><i class="fas fa-store me-2"></i>${sucursal.nombre}</h6>
            <p class="mb-2">${sucursal.direccion}</p>
            <small class="text-muted">Sucursal seleccionada</small>
        </div>
    `).openPopup();
}

// Limpiar mapa
function clearMap() {
    // Verificar que drawnItems esté inicializado antes de usarlo
    if (drawnItems) {
        drawnItems.clearLayers();
    }
    clearExistingPolygons();
    clearSucursalMarker();
    showAlert('Mapa limpiado', 'info');
}

// Alternar sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.style.display = sidebar.style.display === 'none' ? 'block' : 'none';
}

// Mostrar alerta
function showAlert(message, type = 'info') {
    // Crear elemento de alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Actualizar visibilidad del botón de guardar
function updateSaveButtonVisibility(sucursalId) {
    const saveButton = document.getElementById(`btnSaveChanges_${sucursalId}`);
    console.log('updateSaveButtonVisibility llamado para sucursal:', sucursalId);
    console.log('hasUnsavedChanges:', hasUnsavedChanges);
    console.log('saveButton encontrado:', !!saveButton);
    
    if (saveButton) {
        if (hasUnsavedChanges) {
            saveButton.classList.add('visible');
            console.log('Botón de guardar mostrado');
        } else {
            saveButton.classList.remove('visible');
            console.log('Botón de guardar ocultado');
        }
    }
}

// Marcar que hay cambios sin guardar
function markAsChanged(sucursalId) {
    console.log('markAsChanged llamado para sucursal:', sucursalId);
    console.log('Estado anterior de hasUnsavedChanges:', hasUnsavedChanges);
    hasUnsavedChanges = true;
    console.log('Estado nuevo de hasUnsavedChanges:', hasUnsavedChanges);
    updateSaveButtonVisibility(sucursalId);
}

// Guardar cambios de zonas
async function saveZonasChanges(sucursalId) {
    console.log('saveZonasChanges llamado para sucursal:', sucursalId);
    console.log('hasUnsavedChanges:', hasUnsavedChanges);
    
    if (!hasUnsavedChanges) {
        showAlert('No hay cambios para guardar', 'info');
        return;
    }
    
    try {
        // Obtener las zonas modificadas, nuevas y eliminadas
        console.log('Zonas actuales:', zonas);
        console.log('Zonas originales:', originalZonas);
        
        const zonasModificadas = zonas.filter(zona => {
            // Excluir zonas marcadas como eliminadas (las manejaremos por separado)
            if (zona.eliminada) {
                return false;
            }
            
            // Si la zona no tiene ID, es una zona nueva
            if (!zona.id) {
                console.log('Zona nueva encontrada:', zona);
                return true;
            }
            
            // Si la zona tiene ID, verificar si ha sido modificada
            const zonaOriginal = originalZonas.find(orig => orig.id === zona.id);
            if (!zonaOriginal) {
                console.log('Zona original no encontrada, marcando como nueva:', zona);
                return true;
            }
            
            // Comparar campos específicos en lugar de usar JSON.stringify
            const isModified = (
                zona.nombre_zona !== zonaOriginal.nombre_zona ||
                zona.activa !== zonaOriginal.activa ||
                JSON.stringify(zona.poligono_coordenadas) !== JSON.stringify(zonaOriginal.poligono_coordenadas)
            );
            
            if (isModified) {
                console.log('Zona modificada encontrada:', zona);
                console.log('Cambios detectados:');
                console.log('- Nombre:', zona.nombre_zona, 'vs', zonaOriginal.nombre_zona);
                console.log('- Activa:', zona.activa, 'vs', zonaOriginal.activa);
                console.log('- Coordenadas:', zona.poligono_coordenadas, 'vs', zonaOriginal.poligono_coordenadas);
            }
            return isModified;
        });
        
        // Obtener zonas marcadas como eliminadas
        const zonasEliminadas = zonas.filter(zona => zona.eliminada && zona.id);
        console.log('Zonas eliminadas:', zonasEliminadas);
        
        // Verificar si hay cambios para procesar
        if (zonasModificadas.length === 0 && zonasEliminadas.length === 0) {
            showAlert('No hay cambios para guardar', 'info');
            return;
        }
        
        // Preparar mensaje de confirmación
        let confirmMessage = '¿Está seguro que desea guardar los cambios realizados en las zonas de cobertura?\n\n';
        if (zonasModificadas.length > 0) {
            confirmMessage += `• ${zonasModificadas.length} zona(s) modificada(s)\n`;
        }
        if (zonasEliminadas.length > 0) {
            confirmMessage += `• ${zonasEliminadas.length} zona(s) eliminada(s)\n`;
        }
        
        // Mostrar confirmación
        const confirmSave = confirm(confirmMessage);
        if (!confirmSave) {
            return;
        }
        
        // Mostrar indicador de carga
        const saveButton = document.getElementById(`btnSaveChanges_${sucursalId}`);
        const originalContent = saveButton.innerHTML;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        saveButton.disabled = true;
        
        console.log('Zonas a guardar:', zonasModificadas);
        console.log('Zonas a eliminar:', zonasEliminadas);
        
        // Guardar cada zona modificada
        let savedCount = 0;
        for (const zona of zonasModificadas) {
            try {
                const coordenadas = zona.poligono_coordenadas;
                
                console.log('=== INICIANDO GUARDADO DE ZONA ===');
                console.log('Zona a guardar:', zona);
                console.log('Datos a enviar:', {
                    sucursal_id: parseInt(sucursalId),
                    nombre_zona: zona.nombre_zona,
                    poligono_coordenadas: coordenadas,
                    activa: zona.activa !== false
                });
                
                const requestData = {
                    sucursal_id: parseInt(sucursalId),
                    nombre_zona: zona.nombre_zona,
                    poligono_coordenadas: coordenadas,
                    activa: zona.activa !== false
                };
                
                console.log('Realizando petición POST a /api/guardar-zona...');
                const response = await fetchWithRateLimit('/api/guardar-zona', {
                    method: 'POST',
                    body: JSON.stringify(requestData)
                });
                
                console.log('Respuesta recibida:', response.status, response.statusText);
                
                if (response.ok) {
                    const responseData = await response.json();
                    console.log('Zona guardada exitosamente:', responseData);
                    savedCount++;
                } else {
                    const errorData = await response.json();
                    console.error('Error en respuesta:', errorData);
                    throw new Error(errorData.error || 'Error al guardar zona');
                }
                console.log('=== FIN GUARDADO DE ZONA ===');
            } catch (error) {
                console.error('Error guardando zona:', error);
                throw error;
            }
        }
        
        // Procesar zonas eliminadas (llamar API externa y remover del array local)
        let deletedCount = 0;
        for (const zonaEliminada of zonasEliminadas) {
            console.log('Procesando zona eliminada:', zonaEliminada);
            
            try {
                // Llamar al endpoint de eliminación en la API externa
                const nombreZona = zonaEliminada.nombre_zona || zonaEliminada.nombreZona;
                console.log('Eliminando zona en API externa:', {
                    sucursal_id: parseInt(sucursalId),
                    nombre_zona: nombreZona
                });
                
                const deleteResponse = await fetchWithRateLimit('/api/eliminar-zona', {
                    method: 'DELETE',
                    body: JSON.stringify({
                        sucursal_id: parseInt(sucursalId),
                        nombre_zona: nombreZona
                    })
                });
                
                if (deleteResponse.ok) {
                    const deleteData = await deleteResponse.json();
                    console.log('Zona eliminada exitosamente en API externa:', deleteData);
                } else {
                    const errorData = await deleteResponse.json();
                    console.error('Error eliminando zona en API externa:', errorData);
                    throw new Error(errorData.error || 'Error al eliminar zona en API externa');
                }
                
                // Remover la zona del array local solo si la eliminación fue exitosa
                const index = zonas.findIndex(z => z.id === zonaEliminada.id);
                if (index !== -1) {
                    zonas.splice(index, 1);
                    deletedCount++;
                }
                
            } catch (error) {
                console.error('Error eliminando zona:', error);
                throw error;
            }
        }
        
        // Actualizar estado
        console.log('Actualizando estado después del guardado');
        hasUnsavedChanges = false;
        originalZonas = JSON.parse(JSON.stringify(zonas));
        updateSaveButtonVisibility(sucursalId);
        
        // Mostrar mensaje de éxito
        let successMessage = '';
        if (savedCount > 0 && deletedCount > 0) {
            successMessage = `Se guardaron ${savedCount} zona(s) y se eliminaron ${deletedCount} zona(s) exitosamente`;
        } else if (savedCount > 0) {
            successMessage = `Se guardaron exitosamente ${savedCount} zona(s) de cobertura`;
        } else if (deletedCount > 0) {
            successMessage = `Se eliminaron exitosamente ${deletedCount} zona(s) de cobertura`;
        }
        showAlert(successMessage, 'success');
        
        // Recargar zonas para asegurar sincronización
        console.log('Recargando zonas para sincronización');
        loadZonasSucursal(sucursalId);
        
    } catch (error) {
        console.error('Error guardando cambios:', error);
        if (error.message.includes('Rate limit exceeded')) {
            // El error de rate limit ya se maneja en fetchWithRateLimit
            return;
        }
        showAlert(`Error al guardar los cambios: ${error.message}`, 'danger');
    } finally {
        // Restaurar botón
        const saveButton = document.getElementById(`btnSaveChanges_${sucursalId}`);
        if (saveButton) {
            saveButton.innerHTML = '<i class="fas fa-save"></i>';
            saveButton.disabled = false;
        }
    }
}

// =============================================================================
// FUNCIONES DE AUTENTICACIÓN - NUEVO FLUJO
// =============================================================================

// Verificar cookie de autenticación al cargar la página
async function checkAuthCookie() {
    try {
        console.log('Verificando cookie de autenticación...');
        
        // Verificar si existe una cookie de autenticación
        const response = await fetch('/auth/check-cookie', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.hasValidCookie) {
                console.log('Cookie válida encontrada:', data.user);
                authCookie = data.user;
                showNextSection(data.user);
                return true;
            }
        }
        
        console.log('No se encontró cookie válida');
        showLoginSection();
        return false;
        
    } catch (error) {
        console.error('Error verificando cookie de autenticación:', error);
        showLoginSection();
        return false;
    }
}

// Mostrar sección de login
function showLoginSection() {
    console.log('Mostrando sección de login');
    hideAllSections();
    const loginSection = document.getElementById('loginSection');
    if (loginSection) {
        loginSection.style.display = 'block';
        console.log('Sección de login mostrada');
    } else {
        console.error('No se encontró el elemento loginSection');
    }
}

// Mostrar sección de siguiente
function showNextSection(user) {
    console.log('Mostrando sección de siguiente para usuario:', user);
    hideAllSections();
    
    // Actualizar información del usuario
    document.getElementById('userName').textContent = user.name;
    document.getElementById('userEmail').textContent = user.email;
    document.getElementById('userPicture').src = user.picture;
    
    document.getElementById('nextSection').style.display = 'block';
}

// Mostrar sección de error
function showErrorSection(message) {
    console.log('Mostrando sección de error:', message);
    hideAllSections();
    
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorSection').style.display = 'block';
}

// Ocultar todas las secciones
function hideAllSections() {
    document.getElementById('authStatus').style.display = 'none';
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('nextSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
}

// Iniciar autenticación con Google
function initiateGoogleAuth() {
    console.log('Iniciando autenticación con Google...');
    window.location.href = '/auth/login';
}

// Proceder al sistema después de validar usuario
async function proceedToSystem() {
    try {
        console.log('Validando usuario contra la API...');
        
        if (!authCookie) {
            showErrorSection('No se encontró información de autenticación. Por favor, inicie sesión nuevamente.');
            return;
        }
        
        // Validar usuario contra la API
        const response = await fetch(`/auth/verify-user?email=${encodeURIComponent(authCookie.email)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.verified) {
                console.log('Usuario verificado exitosamente');
                // Mostrar pantalla principal del sistema
                showMainSystem(authCookie);
            } else {
                console.log('Usuario no verificado en la API');
                showErrorSection('Su cuenta no está registrada en el sistema. Contacte al administrador para obtener acceso.');
            }
        } else if (response.status === 404) {
            console.log('Usuario no encontrado en la API (404)');
            showErrorSection('Su cuenta no está registrada en el sistema. Contacte al administrador para obtener acceso.');
        } else {
            console.error('Error verificando usuario:', response.status);
            showErrorSection('Error al verificar su cuenta. Intente nuevamente.');
        }
        
    } catch (error) {
        console.error('Error validando usuario:', error);
        showErrorSection('Error de conexión al verificar su cuenta. Intente nuevamente.');
    }
}

// Mostrar pantalla principal del sistema
function showMainSystem(user) {
    console.log('Mostrando pantalla principal del sistema');
    
    // Ocultar pantalla de administración
    document.getElementById('adminScreen').style.display = 'none';
    
    // Mostrar pantalla principal
    document.getElementById('mainSystem').style.display = 'block';
    
    // Actualizar información del usuario en el header
    const userName = document.querySelector('#mainSystem #userName');
    const userPicture = document.querySelector('#mainSystem #userPicture');
    
    if (userName) userName.textContent = user.name;
    if (userPicture) {
        userPicture.src = user.picture;
        userPicture.alt = user.name;
    }
    
    // Establecer variables globales
    isAuthenticated = true;
    currentUser = user;
    
    // Inicializar el sistema
    initializeSystem();
}

// Reiniciar flujo de autenticación
function resetAuthFlow() {
    console.log('Reiniciando flujo de autenticación');
    
    // Limpiar variables
    isAuthenticated = false;
    currentUser = null;
    authCookie = null;
    
    // Ocultar pantalla principal si está visible
    document.getElementById('mainSystem').style.display = 'none';
    
    // Mostrar pantalla de administración
    document.getElementById('adminScreen').style.display = 'block';
    
    // Verificar cookie nuevamente
    checkAuthCookie();
}

// Inicializar el sistema después de la autenticación
async function initializeSystem() {
    try {
        console.log('Inicializando sistema...');
        
        // Inicializar mapa
        initMap();
        
        // Cargar datos iniciales
        await loadInitialData();
        
        console.log('Sistema inicializado exitosamente');
        
    } catch (error) {
        console.error('Error inicializando sistema:', error);
        showAlert('Error al inicializar el sistema', 'danger');
    }
}

// Actualizar la interfaz de usuario según el estado de autenticación
function updateAuthUI(authenticated) {
    const userInfo = document.getElementById('userInfo');
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const userName = document.getElementById('userName');
    const userPicture = document.getElementById('userPicture');
    
    if (authenticated && currentUser) {
        // Usuario autenticado
        userInfo.style.display = 'inline-block';
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
        
        userName.textContent = currentUser.name;
        userPicture.src = currentUser.picture;
        userPicture.alt = currentUser.name;
        
        // Habilitar funcionalidades
        enableAppFeatures();
    } else {
        // Usuario no autenticado
        userInfo.style.display = 'none';
        loginBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        
        // Deshabilitar funcionalidades
        disableAppFeatures();
    }
}

// Cargar datos iniciales después de la autenticación
async function loadInitialData() {
    try {
        console.log('Cargando datos iniciales después de autenticación...');
        await Promise.all([
            loadSucursales(),
            loadZonas()
        ]);
        console.log('Datos iniciales cargados exitosamente');
    } catch (error) {
        console.error('Error cargando datos iniciales:', error);
        // Si hay errores de conectividad, ofrecer reintentar
        if (!error.message.includes('Sesión expirada') && !error.message.includes('Autenticación requerida')) {
            showRetryOption();
        }
    }
}

// Mostrar opción para reintentar carga de datos
function showRetryOption() {
    const retryMessage = `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Error de conectividad</strong><br>
            No se pudieron cargar los datos iniciales. 
            <button class="btn btn-sm btn-warning ms-2" onclick="retryLoadData()">
                <i class="fas fa-redo me-1"></i>Reintentar
            </button>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insertar el mensaje al principio del sidebar
    const sidebar = document.getElementById('sidebar');
    sidebar.insertAdjacentHTML('afterbegin', retryMessage);
}

// Reintentar carga de datos
async function retryLoadData() {
    console.log('Reintentando carga de datos...');
    showAlert('Reintentando carga de datos...', 'info');
    
    try {
        await loadInitialData();
        // Remover el mensaje de reintento si se cargaron exitosamente
        const retryAlert = document.querySelector('.alert-warning');
        if (retryAlert) {
            retryAlert.remove();
        }
    } catch (error) {
        console.error('Error en reintento de carga:', error);
        showAlert('Error al reintentar. Verifique su conexión.', 'danger');
    }
}

// Función para probar manualmente la carga de datos (para debugging)
async function testDataLoading() {
    console.log('=== PRUEBA MANUAL DE CARGA DE DATOS ===');
    
    try {
        console.log('1. Verificando estado de autenticación...');
        console.log('Variables globales:');
        console.log('  - isAuthenticated:', isAuthenticated);
        console.log('  - currentUser:', currentUser);
        
        const authResponse = await fetch('/auth/status', {
            credentials: 'include'
        });
        console.log('Respuesta HTTP:', authResponse.status, authResponse.statusText);
        const authData = await authResponse.json();
        console.log('Estado de autenticación del servidor:', authData);
        
        // Actualizar variables globales con la respuesta del servidor
        if (authData.authenticated) {
            isAuthenticated = true;
            currentUser = authData.user;
            console.log('Variables globales actualizadas:');
            console.log('  - isAuthenticated:', isAuthenticated);
            console.log('  - currentUser:', currentUser);
        } else {
            isAuthenticated = false;
            currentUser = null;
            console.log('Usuario no autenticado según el servidor');
            showAlert('Usuario no autenticado. Por favor, inicie sesión.', 'warning');
            return;
        }
        
        console.log('2. Intentando cargar sucursales...');
        await loadSucursales();
        
        console.log('3. Intentando cargar zonas...');
        await loadZonas();
        
        console.log('=== PRUEBA COMPLETADA ===');
        showAlert('Prueba de carga de datos completada. Revise la consola para detalles.', 'info');
        
    } catch (error) {
        console.error('Error en prueba de carga de datos:', error);
        showAlert('Error en la prueba de carga de datos. Revise la consola para detalles.', 'danger');
    }
}

// Función para verificar el estado de la sesión en el servidor
async function checkServerSession() {
    console.log('=== VERIFICACIÓN DE SESIÓN EN SERVIDOR ===');
    
    try {
        const response = await fetch('/auth/status', {
            credentials: 'include'
        });
        console.log('Respuesta del servidor:', response.status, response.statusText);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Datos de sesión:', data);
            
            if (data.authenticated) {
                console.log('✓ Usuario autenticado en el servidor');
                console.log('Usuario:', data.user);
                return true;
            } else {
                console.log('✗ Usuario NO autenticado en el servidor');
                return false;
            }
        } else {
            console.log('✗ Error en respuesta del servidor:', response.status);
            return false;
        }
    } catch (error) {
        console.error('Error verificando sesión:', error);
        return false;
    }
}

// Función para limpiar datos y reintentar (para debugging)
function resetAndReload() {
    console.log('=== RESET Y RECARGA ===');
    
    // Limpiar datos actuales
    sucursales = [];
    zonas = [];
    currentSucursal = null;
    currentZona = null;
    
    // Limpiar UI
    renderSucursales();
    renderZonas();
    clearMap();
    
    // Verificar sesión en el servidor antes de reintentar
    checkServerSession().then(isAuth => {
        if (isAuth) {
            console.log('Sesión válida encontrada, reintentando carga...');
            setTimeout(() => {
                testDataLoading();
            }, 1000);
        } else {
            console.log('No hay sesión válida, solicitando login...');
            showAlert('Usuario no autenticado. Por favor, inicie sesión.', 'warning');
        }
    });
}

// Habilitar funcionalidades de la aplicación
function enableAppFeatures() {
    // Habilitar botones de la aplicación
    const buttons = document.querySelectorAll('.btn-custom, .btn-success-custom, .btn-danger-custom');
    buttons.forEach(button => {
        button.disabled = false;
    });
    
    // Los datos se cargarán automáticamente en checkAuthStatus
    console.log('Funcionalidades de la aplicación habilitadas');
}

// Deshabilitar funcionalidades de la aplicación
function disableAppFeatures() {
    // Deshabilitar botones de la aplicación
    const buttons = document.querySelectorAll('.btn-custom, .btn-success-custom, .btn-danger-custom');
    buttons.forEach(button => {
        button.disabled = true;
    });
    
    // Limpiar datos
    sucursales = [];
    zonas = [];
    renderSucursales();
    renderZonas();
    clearMap();
}

// Función de logout
async function logout() {
    try {
        console.log('Cerrando sesión...');
        
        const response = await fetch('/auth/logout', {
            credentials: 'include'
        });
        
        if (response.ok) {
            // Limpiar variables globales
            isAuthenticated = false;
            currentUser = null;
            authCookie = null;
            
            // Volver a la pantalla de administración
            resetAuthFlow();
            
            showAlert('Sesión cerrada exitosamente', 'info');
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Error al cerrar sesión');
        }
    } catch (error) {
        console.error('Error cerrando sesión:', error);
        showAlert('Error al cerrar sesión', 'danger');
    }
}

// Verificar autenticación antes de realizar acciones protegidas
function requireAuth(callback) {
    if (isAuthenticated) {
        callback();
    } else {
        showAuthModal();
    }
}

// Mostrar modal de autenticación
function showAuthModal() {
    const modal = new bootstrap.Modal(document.getElementById('authModal'));
    modal.show();
}

// Interceptar llamadas a la API para manejar errores de autenticación
async function apiCall(url, options = {}) {
    try {
        console.log(`Realizando llamada a API: ${url}`);
        const response = await fetchWithRateLimit(url, options);
        
        console.log(`Respuesta de API ${url}: ${response.status} ${response.statusText}`);
        
        // Si la respuesta es 401 (No autorizado), redirigir al login
        if (response.status === 401) {
            console.log('Error 401: Sesión expirada, redirigiendo al login');
            isAuthenticated = false;
            currentUser = null;
            updateAuthUI(false);
            showAuthModal();
            throw new Error('Sesión expirada. Por favor, inicie sesión nuevamente.');
        }
        
        // Si la respuesta es 403 (Prohibido), mostrar mensaje de permisos
        if (response.status === 403) {
            console.log('Error 403: Acceso denegado');
            showAlert('No tiene permisos para realizar esta acción', 'warning');
            throw new Error('Acceso denegado');
        }
        
        return response;
    } catch (error) {
        console.error(`Error en llamada a API ${url}:`, error);
        if (error.message.includes('Sesión expirada') || error.message.includes('Acceso denegado')) {
            throw error;
        }
        throw new Error(`Error en la API: ${error.message}`);
    }
}

// Inicializar aplicación
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== INICIALIZANDO APLICACIÓN ===');
    
    // Verificar que los elementos HTML estén presentes
    const adminScreen = document.getElementById('adminScreen');
    const mainSystem = document.getElementById('mainSystem');
    const loginSection = document.getElementById('loginSection');
    
    console.log('Elementos HTML encontrados:');
    console.log('- adminScreen:', !!adminScreen);
    console.log('- mainSystem:', !!mainSystem);
    console.log('- loginSection:', !!loginSection);
    
    if (!adminScreen) {
        console.error('ERROR: No se encontró el elemento adminScreen');
        return;
    }
    
    // Asegurar que la pantalla de administración esté visible inicialmente
    adminScreen.style.display = 'block';
    if (mainSystem) {
        mainSystem.style.display = 'none';
    }
    
    // Inicializar sistema de rate limiting
    initializeRateLimiting();
    
    // Verificar cookie de autenticación
    checkAuthCookie().then(() => {
        console.log('Verificación de cookie completada');
    }).catch(error => {
        console.error('Error verificando cookie de autenticación:', error);
    });
    
    // Event listener para Enter en consulta de dirección (solo cuando el sistema esté cargado)
    const direccionInput = document.getElementById('direccionConsulta');
    if (direccionInput) {
        direccionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                requireAuth(() => consultarDireccion());
            }
        });
    }
    
    console.log('=== APLICACIÓN INICIALIZADA ===');
});

// Inicializar sistema de rate limiting
function initializeRateLimiting() {
    console.log('Inicializando sistema de rate limiting...');
    console.log('Session ID:', sessionId);
    console.log('Client Fingerprint:', clientFingerprint);
    
    // Crear RateLimitInfo inicial
    rateLimitInfo = createRateLimitInfo();
    
    // Ejecutar prueba del sistema
    testRateLimiting();
    
    // Mostrar información inicial
    showAlert('Sistema de rate limiting inicializado', 'info');
}
