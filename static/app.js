// Variables globales
let map;
let drawnItems;
let drawControl;
let currentSucursal = null;
let currentZona = null;
let isDrawingMode = false;
let sucursales = [];
let zonas = [];

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
        }
    });
    
    map.on(L.Draw.Event.EDITED, function(event) {
        console.log('Polígono editado');
    });
    
    map.on(L.Draw.Event.DELETED, function(event) {
        console.log('Polígono eliminado');
    });
    
    // Cargar datos iniciales
    loadSucursales();
    loadZonas();
}

// Cargar sucursales
async function loadSucursales() {
    try {
        const response = await fetch('/api/sucursales');
        sucursales = await response.json();
        renderSucursales();
    } catch (error) {
        console.error('Error cargando sucursales:', error);
        showAlert('Error al cargar sucursales', 'danger');
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
                <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); showSucursalOnMap(${sucursal.id})">
                    <i class="fas fa-map-marker-alt"></i>
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="event.stopPropagation(); createZoneForSucursal(${sucursal.id})">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Cargar zonas de cobertura
async function loadZonas() {
    try {
        const response = await fetch('/api/zonas');
        zonas = await response.json();
        renderZonas();
        renderZonasOnMap();
    } catch (error) {
        console.error('Error cargando zonas:', error);
        showAlert('Error al cargar zonas', 'danger');
    }
}

// Cargar zonas de cobertura para una sucursal específica
async function loadZonasSucursal(sucursalId) {
    try {
        const response = await fetch(`/api/zonas/${sucursalId}`);
        if (response.ok) {
            const zonasSucursal = await response.json();
            // Actualizar la lista de zonas con las de la sucursal seleccionada
            zonas = zonasSucursal;
            renderZonas();
            renderZonasOnMap();
        } else {
            console.warn(`No se encontraron zonas para la sucursal ${sucursalId}`);
            zonas = [];
            renderZonas();
            renderZonasOnMap();
        }
    } catch (error) {
        console.error('Error cargando zonas de sucursal:', error);
        showAlert('Error al cargar zonas de la sucursal', 'danger');
    }
}

// Renderizar zonas en la lista
function renderZonas() {
    const container = document.getElementById('listaZonas');
    
    if (zonas.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay zonas de cobertura</p>';
        return;
    }
    
    container.innerHTML = zonas.map(zona => {
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
                    <button class="btn btn-sm btn-outline-warning" onclick="editZonaCalles(${zonaId})">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Renderizar zonas en el mapa
function renderZonasOnMap() {
    // Limpiar zonas existentes
    map.eachLayer(layer => {
        if (layer.options && layer.options.isZona) {
            map.removeLayer(layer);
        }
    });
    
    zonas.forEach(zona => {
        try {
            let coordenadas;
            
            // Manejar diferentes formatos de coordenadas
            if (typeof zona.poligono_coordenadas === 'string') {
                coordenadas = JSON.parse(zona.poligono_coordenadas);
            } else {
                coordenadas = zona.poligono_coordenadas;
            }
            
            // Convertir coordenadas al formato esperado por Leaflet
            const latLngs = coordenadas.map(coord => {
                if (Array.isArray(coord)) {
                    // Formato [lat, lng]
                    return [coord[0], coord[1]];
                } else {
                    // Formato {latitud, longitud}
                    return [coord.latitud, coord.longitud];
                }
            });
            
            const polygon = L.polygon(latLngs, {
                color: '#28a745',
                fillColor: '#28a745',
                fillOpacity: 0.3,
                isZona: true,
                zonaId: zona.id || zona.zonaId
            }).addTo(map);
            
            const sucursalNombre = zona.sucursal_nombre || 
                                 (currentSucursal ? currentSucursal.nombre : 'Sucursal');
            
            polygon.bindPopup(`
                <strong>${zona.nombre_zona || zona.nombreZona}</strong><br>
                Sucursal: ${sucursalNombre}<br>
                <button class="btn btn-sm btn-primary mt-2" onclick="editZonaCalles(${zona.id || zona.zonaId})">
                    Editar Calles
                </button>
            `);
        } catch (error) {
            console.error('Error renderizando zona:', error);
        }
    });
}

// Seleccionar sucursal
function selectSucursal(sucursalId) {
    // Remover selección anterior
    document.querySelectorAll('.sucursal-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Seleccionar nueva sucursal
    const item = document.querySelector(`[data-id="${sucursalId}"]`);
    if (item) {
        item.classList.add('active');
        currentSucursal = sucursales.find(s => s.id === sucursalId);
        
        // Cargar zonas específicas para esta sucursal
        loadZonasSucursal(sucursalId);
    }
}

// Mostrar sucursal en el mapa
function showSucursalOnMap(sucursalId) {
    const sucursal = sucursales.find(s => s.id === sucursalId);
    if (sucursal) {
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
            
            // Convertir coordenadas al formato esperado por Leaflet
            const latLngs = coordenadas.map(coord => {
                if (Array.isArray(coord)) {
                    // Formato [lat, lng]
                    return [coord[0], coord[1]];
                } else {
                    // Formato {latitud, longitud}
                    return [coord.latitud, coord.longitud];
                }
            });
            
            const bounds = L.polygon(latLngs).getBounds();
            map.fitBounds(bounds);
        } catch (error) {
            console.error('Error mostrando zona:', error);
        }
    }
}

// Crear zona para sucursal
function createZoneForSucursal(sucursalId) {
    currentSucursal = sucursales.find(s => s.id === sucursalId);
    startDrawingZone();
}

// Iniciar modo de dibujo
function startDrawingZone() {
    if (!currentSucursal) {
        showAlert('Por favor seleccione una sucursal primero', 'warning');
        return;
    }
    
    isDrawingMode = true;
    document.getElementById('btnDrawZone').innerHTML = '<i class="fas fa-stop me-2"></i>Cancelar Dibujo';
    document.getElementById('btnDrawZone').onclick = cancelDrawing;
    
    showAlert('Dibuje un polígono en el mapa para definir la zona de cobertura', 'info');
}

// Cancelar dibujo
function cancelDrawing() {
    isDrawingMode = false;
    document.getElementById('btnDrawZone').innerHTML = '<i class="fas fa-draw-polygon me-2"></i>Dibujar Zona';
    document.getElementById('btnDrawZone').onclick = startDrawingZone;
    
    // Limpiar elementos dibujados
    drawnItems.clearLayers();
}

// Mostrar modal de zona
function showZonaModal(layer) {
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
    const sucursalId = document.getElementById('sucursalZona').value;
    const nombreZona = document.getElementById('nombreZona').value;
    
    if (!sucursalId || !nombreZona) {
        showAlert('Por favor complete todos los campos', 'warning');
        return;
    }
    
    if (!currentZona) {
        showAlert('No hay polígono dibujado', 'error');
        return;
    }
    
    try {
        const coordenadas = currentZona.getLatLngs()[0].map(latlng => ({
            latitud: latlng.lat,
            longitud: latlng.lng
        }));
        
        const response = await fetch('/api/guardar-zona', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sucursal_id: parseInt(sucursalId),
                nombre_zona: nombreZona,
                poligono_coordenadas: coordenadas,
                activa: true,
                calles: [] // Las calles se pueden agregar después
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            showAlert('Zona creada exitosamente', 'success');
            bootstrap.Modal.getInstance(document.getElementById('modalZona')).hide();
            
            // Limpiar formulario
            document.getElementById('formZona').reset();
            drawnItems.clearLayers();
            
            // Recargar zonas para la sucursal seleccionada
            if (currentSucursal) {
                loadZonasSucursal(currentSucursal.id);
            } else {
                loadZonas();
            }
            
            // Salir del modo dibujo
            cancelDrawing();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al crear zona');
        }
    } catch (error) {
        console.error('Error guardando zona:', error);
        showAlert(`Error al guardar la zona: ${error.message}`, 'danger');
    }
}

// Mostrar modal de nueva sucursal
function showCreateSucursalModal() {
    document.getElementById('formSucursal').reset();
    const modal = new bootstrap.Modal(document.getElementById('modalSucursal'));
    modal.show();
}

// Guardar sucursal
async function saveSucursal() {
    const nombre = document.getElementById('nombreSucursal').value;
    const direccion = document.getElementById('direccionSucursal').value;
    const latitud = parseFloat(document.getElementById('latitudSucursal').value);
    const longitud = parseFloat(document.getElementById('longitudSucursal').value);
    
    if (!nombre || !direccion || isNaN(latitud) || isNaN(longitud)) {
        showAlert('Por favor complete todos los campos correctamente', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/sucursales', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nombre: nombre,
                direccion: direccion,
                latitud: latitud,
                longitud: longitud
            })
        });
        
        if (response.ok) {
            showAlert('Sucursal creada exitosamente', 'success');
            bootstrap.Modal.getInstance(document.getElementById('modalSucursal')).hide();
            
            // Limpiar formulario
            document.getElementById('formSucursal').reset();
            
            // Recargar sucursales
            loadSucursales();
        } else {
            throw new Error('Error al crear sucursal');
        }
    } catch (error) {
        console.error('Error guardando sucursal:', error);
        showAlert('Error al guardar la sucursal', 'danger');
    }
}

// Consultar dirección
async function consultarDireccion() {
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
        const response = await fetch('/api/consultar-cobertura', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
        resultadoContainer.innerHTML = `
            <div class="alert alert-danger alert-custom">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error al consultar la dirección
            </div>
        `;
    }
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
    map.setView([lat, lng], 16);
    
    L.marker([lat, lng])
        .addTo(map)
        .bindPopup('Dirección consultada')
        .openPopup();
}

// Editar calles de zona
async function editZonaCalles(zonaId) {
    currentZona = zonas.find(z => (z.id === zonaId) || (z.zonaId === zonaId));
    
    const modal = new bootstrap.Modal(document.getElementById('modalCalles'));
    modal.show();
    
    // Mostrar loading
    document.getElementById('contenidoCalles').innerHTML = `
        <div class="loading">
            <div class="spinner-border spinner-border-custom" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2">Procesando calles de la zona...</p>
        </div>
    `;
    
    try {
        // Simular procesamiento de calles (aquí implementarías la lógica real)
        setTimeout(() => {
            renderCallesZona(zonaId);
        }, 2000);
    } catch (error) {
        console.error('Error procesando calles:', error);
    }
}

// Renderizar calles de zona
function renderCallesZona(zonaId) {
    const container = document.getElementById('contenidoCalles');
    
    // Obtener calles de la zona actual o usar datos simulados
    const callesZona = currentZona.calles || [];
    const nombreZona = currentZona.nombre_zona || currentZona.nombreZona;
    
    // Si no hay calles, usar datos simulados
    const callesSimuladas = callesZona.length > 0 ? callesZona : [
        { nombre_calle: 'Av. Corrientes', altura_desde: 100, altura_hasta: 2000 },
        { nombre_calle: 'Av. Santa Fe', altura_desde: 500, altura_hasta: 3000 },
        { nombre_calle: 'Av. Córdoba', altura_desde: 200, altura_hasta: 2500 }
    ];
    
    container.innerHTML = `
        <div class="mb-3">
            <h6>Zona: ${nombreZona}</h6>
            <p class="text-muted">Edite las alturas de las calles que están en esta zona de cobertura:</p>
        </div>
        
        <div id="listaCalles">
            ${callesSimuladas.map((calle, index) => `
                <div class="row mb-3">
                    <div class="col-5">
                        <input type="text" class="form-control" value="${calle.nombre_calle || calle.nombreCalle}" readonly>
                    </div>
                    <div class="col-3">
                        <input type="number" class="form-control altura-desde" value="${calle.altura_desde || calle.alturaDesde}" placeholder="Desde">
                    </div>
                    <div class="col-3">
                        <input type="number" class="form-control altura-hasta" value="${calle.altura_hasta || calle.alturaHasta}" placeholder="Hasta">
                    </div>
                    <div class="col-1">
                        <button class="btn btn-sm btn-outline-danger" onclick="removeCalle(${index})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
        
        <div class="text-center">
            <button class="btn btn-outline-primary" onclick="addCalle()">
                <i class="fas fa-plus me-2"></i>Agregar Calle
            </button>
        </div>
    `;
}

// Agregar calle
function addCalle() {
    const container = document.getElementById('listaCalles');
    const index = container.children.length;
    
    const nuevaCalle = `
        <div class="row mb-3">
            <div class="col-5">
                <input type="text" class="form-control nombre-calle" placeholder="Nombre de la calle">
            </div>
            <div class="col-3">
                <input type="number" class="form-control altura-desde" placeholder="Desde">
            </div>
            <div class="col-3">
                <input type="number" class="form-control altura-hasta" placeholder="Hasta">
            </div>
            <div class="col-1">
                <button class="btn btn-sm btn-outline-danger" onclick="removeCalle(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', nuevaCalle);
}

// Remover calle
function removeCalle(index) {
    const container = document.getElementById('listaCalles');
    const fila = container.children[index];
    if (fila) {
        fila.remove();
    }
}

// Guardar calles
async function saveCalles() {
    const filas = document.querySelectorAll('#listaCalles .row');
    const calles = [];
    
    filas.forEach(fila => {
        const nombreCalle = fila.querySelector('.nombre-calle, input[readonly]')?.value;
        const alturaDesde = parseInt(fila.querySelector('.altura-desde')?.value);
        const alturaHasta = parseInt(fila.querySelector('.altura-hasta')?.value);
        
        if (nombreCalle && !isNaN(alturaDesde) && !isNaN(alturaHasta)) {
            calles.push({
                nombre_calle: nombreCalle,
                altura_desde: alturaDesde,
                altura_hasta: alturaHasta
            });
        }
    });
    
    try {
        const zonaId = currentZona.id || currentZona.zonaId;
        const response = await fetch('/api/guardar-calles-zona', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                zona_id: zonaId,
                calles: calles
            })
        });
        
        if (response.ok) {
            showAlert('Calles guardadas exitosamente', 'success');
            bootstrap.Modal.getInstance(document.getElementById('modalCalles')).hide();
        } else {
            throw new Error('Error al guardar calles');
        }
    } catch (error) {
        console.error('Error guardando calles:', error);
        showAlert('Error al guardar las calles', 'danger');
    }
}

// Limpiar mapa
function clearMap() {
    drawnItems.clearLayers();
    map.eachLayer(layer => {
        if (layer.options && layer.options.isZona) {
            map.removeLayer(layer);
        }
    });
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

// Inicializar aplicación
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    
    // Event listener para Enter en consulta de dirección
    document.getElementById('direccionConsulta').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            consultarDireccion();
        }
    });
});
