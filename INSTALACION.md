# 🚀 Instalación Rápida - Sistema de Zonas de Cobertura

## ⚡ Instalación en 3 Pasos

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la Aplicación
```bash
python app.py
```
*O usar el script mejorado:*
```bash
python run.py
```

### 3. Abrir en el Navegador
```
http://localhost:5000
```

## 🎯 Datos de Prueba (Opcional)

Para cargar datos de ejemplo:
```bash
python sample_data.py
```

Esto creará:
- 3 sucursales de ejemplo en Buenos Aires
- 3 zonas de cobertura
- Calles con rangos de altura

## 🔧 Solución de Problemas

### Error: "No module named 'flask'"
```bash
pip install flask flask-cors requests geopy shapely
```

### Error: "Permission denied" en Windows
Ejecutar PowerShell como Administrador

### Puerto 5000 ocupado
Cambiar el puerto en `app.py` línea final:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Cambiar 5000 por 5001
```

### Problemas con geocodificación
- Verificar conexión a internet
- El servicio Nominatim tiene límites de uso

## 📱 Uso Básico

1. **Crear Sucursal**: Botón "Nueva Sucursal"
2. **Dibujar Zona**: Seleccionar sucursal → "Dibujar Zona" → Dibujar polígono
3. **Consultar Dirección**: Ingresar dirección → Buscar
4. **Editar Calles**: Hacer clic en zona → "Editar Calles"

## 🆘 Soporte

- Revisar `README.md` para documentación completa
- Verificar logs en consola
- Comprobar que Python 3.7+ esté instalado

¡Listo! 🎉
