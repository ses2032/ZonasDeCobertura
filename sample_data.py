#!/usr/bin/env python3
# =============================================================================
# SCRIPT PARA CARGAR DATOS DE EJEMPLO EN EL SISTEMA
# =============================================================================
"""
Este script carga datos de ejemplo en la base de datos del sistema para
facilitar las pruebas y demostraciones. Los datos incluyen:

1. Sucursales de ejemplo en Buenos Aires
2. Zonas de cobertura dibujadas para cada sucursal
3. Calles y rangos de altura para cada zona

Uso:
    python sample_data.py

Los datos se cargan en la base de datos SQLite local y pueden ser
utilizados para probar todas las funcionalidades del sistema.
"""

# =============================================================================
# IMPORTS - Importación de librerías necesarias
# =============================================================================

# sqlite3: Para conectarse a la base de datos SQLite
import sqlite3
# json: Para manejar datos en formato JSON (coordenadas de polígonos)
import json

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def load_sample_data():
    """
    Carga datos de ejemplo en la base de datos del sistema.
    
    Esta función crea datos de prueba que incluyen sucursales, zonas de
    cobertura y calles asociadas. Los datos se basan en ubicaciones reales
    de Buenos Aires para hacer las pruebas más realistas.
    """
    
    # =====================================================================
    # CONEXIÓN A LA BASE DE DATOS
    # =====================================================================
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('zonas_cobertura.db')
    # Crear un cursor para ejecutar comandos SQL
    cursor = conn.cursor()
    
    print("🔄 Cargando datos de ejemplo...")
    
    # =====================================================================
    # LIMPIEZA DE DATOS EXISTENTES
    # =====================================================================
    # Eliminar datos existentes en orden inverso a las relaciones
    # (primero las tablas que dependen de otras)
    cursor.execute('DELETE FROM calles_cobertura')  # Eliminar calles
    cursor.execute('DELETE FROM zonas_cobertura')   # Eliminar zonas
    cursor.execute('DELETE FROM sucursales')        # Eliminar sucursales
    
    # =====================================================================
    # DATOS DE SUCURSALES DE EJEMPLO
    # =====================================================================
    # Lista de sucursales con ubicaciones reales en Buenos Aires
    # Cada sucursal tiene nombre, dirección y coordenadas geográficas
    sucursales = [
        {
            'nombre': 'Sucursal Centro',
            'direccion': 'Av. Corrientes 1234, CABA',
            'latitud': -34.6037,   # Coordenada Y (norte-sur)
            'longitud': -58.3816   # Coordenada X (este-oeste)
        },
        {
            'nombre': 'Sucursal Palermo',
            'direccion': 'Av. Santa Fe 4567, CABA',
            'latitud': -34.5889,   # Coordenada Y (norte-sur)
            'longitud': -58.3974   # Coordenada X (este-oeste)
        },
        {
            'nombre': 'Sucursal Belgrano',
            'direccion': 'Av. Cabildo 2345, CABA',
            'latitud': -34.5627,   # Coordenada Y (norte-sur)
            'longitud': -58.4580   # Coordenada X (este-oeste)
        }
    ]
    
    # =====================================================================
    # INSERCIÓN DE SUCURSALES
    # =====================================================================
    # Lista para almacenar los IDs de las sucursales creadas
    # (necesarios para crear las zonas de cobertura)
    sucursal_ids = []
    
    # Recorrer cada sucursal e insertarla en la base de datos
    for sucursal in sucursales:
        # Insertar la sucursal en la tabla 'sucursales'
        cursor.execute('''
            INSERT INTO sucursales (nombre, direccion, latitud, longitud)
            VALUES (?, ?, ?, ?)
        ''', (sucursal['nombre'], sucursal['direccion'], 
              sucursal['latitud'], sucursal['longitud']))
        
        # Guardar el ID de la sucursal recién creada
        sucursal_ids.append(cursor.lastrowid)
    
    print(f"✅ {len(sucursales)} sucursales creadas")
    
    # =====================================================================
    # DATOS DE ZONAS DE COBERTURA DE EJEMPLO
    # =====================================================================
    # Lista de zonas de cobertura (polígonos) para cada sucursal
    # Cada zona define un área geográfica donde la sucursal puede hacer delivery
    zonas = [
        {
            'sucursal_id': sucursal_ids[0],  # ID de la Sucursal Centro
            'nombre_zona': 'Zona Centro Norte',
            # Lista de coordenadas que forman el polígono de la zona
            # Cada coordenada es [latitud, longitud]
            'poligono_coordenadas': [
                [-34.6037, -58.3816],  # Punto 1: esquina superior izquierda
                [-34.6000, -58.3750],  # Punto 2: esquina superior derecha
                [-34.5950, -58.3750],  # Punto 3: esquina inferior derecha
                [-34.5950, -58.3850],  # Punto 4: esquina inferior izquierda
                [-34.6037, -58.3850]   # Punto 5: cierra el polígono (igual al punto 1)
            ]
        },
        {
            'sucursal_id': sucursal_ids[1],  # ID de la Sucursal Palermo
            'nombre_zona': 'Zona Palermo',
            'poligono_coordenadas': [
                [-34.5889, -58.3974],  # Punto 1: esquina superior izquierda
                [-34.5850, -58.3900],  # Punto 2: esquina superior derecha
                [-34.5800, -58.3900],  # Punto 3: esquina inferior derecha
                [-34.5800, -58.4000],  # Punto 4: esquina inferior izquierda
                [-34.5889, -58.4000]   # Punto 5: cierra el polígono
            ]
        },
        {
            'sucursal_id': sucursal_ids[2],  # ID de la Sucursal Belgrano
            'nombre_zona': 'Zona Belgrano',
            'poligono_coordenadas': [
                [-34.5627, -58.4580],  # Punto 1: esquina superior izquierda
                [-34.5600, -58.4500],  # Punto 2: esquina superior derecha
                [-34.5550, -58.4500],  # Punto 3: esquina inferior derecha
                [-34.5550, -58.4600],  # Punto 4: esquina inferior izquierda
                [-34.5627, -58.4600]   # Punto 5: cierra el polígono
            ]
        }
    ]
    
    # =====================================================================
    # INSERCIÓN DE ZONAS DE COBERTURA
    # =====================================================================
    # Lista para almacenar los IDs de las zonas creadas
    # (necesarios para crear las calles asociadas)
    zona_ids = []
    
    # Recorrer cada zona e insertarla en la base de datos
    for zona in zonas:
        # Insertar la zona en la tabla 'zonas_cobertura'
        # json.dumps() convierte la lista de coordenadas a una cadena JSON
        cursor.execute('''
            INSERT INTO zonas_cobertura (sucursal_id, nombre_zona, poligono_coordenadas)
            VALUES (?, ?, ?)
        ''', (zona['sucursal_id'], zona['nombre_zona'], 
              json.dumps(zona['poligono_coordenadas'])))
        
        # Guardar el ID de la zona recién creada
        zona_ids.append(cursor.lastrowid)
    
    print(f"✅ {len(zonas)} zonas de cobertura creadas")
    
    # =====================================================================
    # DATOS DE CALLES DE EJEMPLO
    # =====================================================================
    # Lista de calles para cada zona de cobertura
    # Cada calle tiene un rango de alturas (desde-hasta) que está cubierto
    calles_por_zona = [
        # Zona Centro Norte (índice 0)
        [
            {'nombre_calle': 'Av. Corrientes', 'altura_desde': 100, 'altura_hasta': 2000},
            {'nombre_calle': 'Av. Santa Fe', 'altura_desde': 500, 'altura_hasta': 3000},
            {'nombre_calle': 'Av. Córdoba', 'altura_desde': 200, 'altura_hasta': 2500},
            {'nombre_calle': 'Av. Callao', 'altura_desde': 100, 'altura_hasta': 1500}
        ],
        # Zona Palermo (índice 1)
        [
            {'nombre_calle': 'Av. Santa Fe', 'altura_desde': 3000, 'altura_hasta': 5000},
            {'nombre_calle': 'Av. Córdoba', 'altura_desde': 2500, 'altura_hasta': 4000},
            {'nombre_calle': 'Av. Coronel Díaz', 'altura_desde': 100, 'altura_hasta': 2000},
            {'nombre_calle': 'Av. Scalabrini Ortiz', 'altura_desde': 200, 'altura_hasta': 1800}
        ],
        # Zona Belgrano (índice 2)
        [
            {'nombre_calle': 'Av. Cabildo', 'altura_desde': 1000, 'altura_hasta': 3000},
            {'nombre_calle': 'Av. Monroe', 'altura_desde': 100, 'altura_hasta': 2000},
            {'nombre_calle': 'Av. Juramento', 'altura_desde': 200, 'altura_hasta': 1500},
            {'nombre_calle': 'Av. Luis María Campos', 'altura_desde': 100, 'altura_hasta': 1200}
        ]
    ]
    
    # =====================================================================
    # INSERCIÓN DE CALLES
    # =====================================================================
    # Contador para el total de calles insertadas
    total_calles = 0
    
    # Recorrer cada zona y sus calles asociadas
    for i, calles in enumerate(calles_por_zona):
        # Recorrer cada calle de la zona actual
        for calle in calles:
            # Insertar la calle en la tabla 'calles_cobertura'
            cursor.execute('''
                INSERT INTO calles_cobertura (zona_id, nombre_calle, altura_desde, altura_hasta)
                VALUES (?, ?, ?, ?)
            ''', (zona_ids[i], calle['nombre_calle'], 
                  calle['altura_desde'], calle['altura_hasta']))
            # Incrementar el contador de calles
            total_calles += 1
    
    print(f"✅ {total_calles} calles creadas")
    
    # =====================================================================
    # FINALIZACIÓN Y CONFIRMACIÓN
    # =====================================================================
    # Confirmar todos los cambios en la base de datos
    conn.commit()
    # Cerrar la conexión para liberar recursos
    conn.close()
    
    # =====================================================================
    # RESUMEN FINAL
    # =====================================================================
    print("\n🎉 Datos de ejemplo cargados exitosamente!")
    print("\n📋 Resumen:")
    print(f"   • {len(sucursales)} sucursales")
    print(f"   • {len(zonas)} zonas de cobertura")
    print(f"   • {total_calles} calles con rangos de altura")
    
    print("\n🌐 Puede acceder a la aplicación en: http://localhost:5000")
    print("💡 Use las direcciones de ejemplo para probar la consulta de cobertura")

# =============================================================================
# PUNTO DE ENTRADA DEL SCRIPT
# =============================================================================

if __name__ == '__main__':
    """
    Esta condición verifica si el script se está ejecutando directamente
    (no importado como módulo). Solo en ese caso se ejecuta la función load_sample_data().
    
    Esto permite que el archivo pueda ser importado sin ejecutar automáticamente
    la carga de datos, lo cual es útil para testing o importación en otros módulos.
    """
    load_sample_data()
