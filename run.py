#!/usr/bin/env python3
# =============================================================================
# SCRIPT DE INICIO PARA EL SISTEMA DE ZONAS DE COBERTURA
# =============================================================================
"""
Este script es el punto de entrada principal para ejecutar la aplicación
del Sistema de Zonas de Cobertura. Se encarga de:

1. Verificar que Python tenga la versión correcta
2. Inicializar la base de datos
3. Verificar que todas las dependencias estén instaladas
4. Mostrar información del sistema
5. Iniciar el servidor Flask

Uso:
    python run.py

El shebang (#!/usr/bin/env python3) permite ejecutar el script directamente
en sistemas Unix/Linux con: ./run.py
"""

# =============================================================================
# IMPORTS - Importación de librerías necesarias
# =============================================================================

# os: Para operaciones del sistema operativo
import os
# sys: Para acceso a información del sistema y salida del programa
import sys
# Importar la aplicación Flask
from app import app

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """
    Función principal para iniciar la aplicación.
    
    Esta función ejecuta todos los pasos necesarios para iniciar la aplicación:
    verificación de requisitos, inicialización de la base de datos, verificación
    de dependencias, y finalmente el inicio del servidor Flask.
    """
    
    # =====================================================================
    # ENCABEZADO DE BIENVENIDA
    # =====================================================================
    print("=" * 60)
    print("🚀 Sistema de Zonas de Cobertura - Delivery")
    print("=" * 60)
    
    # =====================================================================
    # VERIFICACIÓN DE VERSIÓN DE PYTHON
    # =====================================================================
    # Verificar que la versión de Python sea 3.7 o superior
    # sys.version_info es una tupla con (major, minor, micro)
    if sys.version_info < (3, 7):
        print("❌ Error: Se requiere Python 3.7 o superior")
        # sys.exit(1) termina el programa con código de error 1
        sys.exit(1)
    
    # Mostrar la versión de Python detectada
    print(f"✅ Python {sys.version.split()[0]} detectado")
    
    
    # =====================================================================
    # VERIFICACIÓN DE DEPENDENCIAS
    # =====================================================================
    try:
        # Intentar importar todas las librerías necesarias
        import flask      # Framework web
        import requests   # Para peticiones HTTP
        import geopy      # Para geocodificación
        import shapely    # Para operaciones geométricas
        print("✅ Todas las dependencias están instaladas")
    except ImportError as e:
        # Si falta alguna dependencia, mostrar el error y cómo solucionarlo
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecute: pip install -r requirements.txt")
        sys.exit(1)
    
    # =====================================================================
    # INFORMACIÓN DEL SISTEMA
    # =====================================================================
    print("\n📋 Información del Sistema:")
    print(f"   • Puerto: 5000")
    print(f"   • Modo: {'Desarrollo' if app.debug else 'Producción'}")
    print(f"   • Mapa por defecto: Buenos Aires, Argentina")
    
    print("\n🌐 Acceso:")
    print("   • Aplicación: http://localhost:5000")
    print("   • API: http://localhost:5000/api/")
    
    print("\n📚 Funcionalidades:")
    print("   • ✅ Gestión de sucursales")
    print("   • ✅ Dibujo de zonas de cobertura")
    print("   • ✅ Consulta de direcciones")
    print("   • ✅ Gestión de calles y alturas")
    print("   • ✅ Mapa interactivo")
    
    # =====================================================================
    # INICIO DEL SERVIDOR
    # =====================================================================
    print("\n" + "=" * 60)
    print("🎯 Iniciando servidor...")
    print("   Presione Ctrl+C para detener")
    print("=" * 60)
    
    try:
        # Iniciar el servidor Flask con configuración específica
        app.run(
            host='0.0.0.0',    # Escuchar en todas las interfaces de red
            port=5000,         # Puerto donde correrá la aplicación
            debug=True,        # Modo debug activado (recarga automática)
            use_reloader=True  # Recargar automáticamente cuando cambien los archivos
        )
    except KeyboardInterrupt:
        # Si el usuario presiona Ctrl+C, mostrar mensaje de despedida
        print("\n\n👋 Servidor detenido por el usuario")
    except Exception as e:
        # Si hay algún error inesperado al iniciar el servidor
        print(f"\n❌ Error iniciando servidor: {e}")
        sys.exit(1)

# =============================================================================
# PUNTO DE ENTRADA DEL SCRIPT
# =============================================================================

if __name__ == '__main__':
    """
    Esta condición verifica si el script se está ejecutando directamente
    (no importado como módulo). Solo en ese caso se ejecuta la función main().
    
    Esto permite que el archivo pueda ser importado sin ejecutar automáticamente
    la función main(), lo cual es útil para testing o importación en otros módulos.
    """
    main()
