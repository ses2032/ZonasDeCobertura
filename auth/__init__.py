# =============================================================================
# PAQUETE DE AUTENTICACIÓN - GOOGLE OAUTH Y VERIFICACIÓN DE USUARIOS
# =============================================================================
"""
Paquete de autenticación para el Sistema de Zonas de Cobertura.

Este paquete contiene toda la lógica de autenticación de la aplicación:
- Autenticación con Google OAuth
- Verificación de usuarios registrados en la API externa
- Gestión de sesiones de usuario
- Middleware de autorización para rutas protegidas

Módulos:
- auth: Funcionalidades principales de autenticación
- test_auth: Pruebas de autenticación
"""

# =============================================================================
# IMPORTS - Importación de funciones principales del módulo auth
# =============================================================================

from .auth import (
    # Configuración de OAuth
    init_oauth,
    
    # Servicio de verificación de usuarios
    UserVerificationService,
    get_user_verification_service,
    
    # Funciones de autenticación
    login_required,
    get_current_user,
    is_user_authenticated,
    logout_user,
    
    # Registro de rutas
    register_auth_routes,
    register_verify_user_route
)

# =============================================================================
# EXPORTS - Funciones y clases que se pueden importar desde este paquete
# =============================================================================

__all__ = [
    # Configuración de OAuth
    'init_oauth',
    
    # Servicio de verificación de usuarios
    'UserVerificationService',
    'get_user_verification_service',
    
    # Funciones de autenticación
    'login_required',
    'get_current_user',
    'is_user_authenticated',
    'logout_user',
    
    # Registro de rutas
    'register_auth_routes',
    'register_verify_user_route'
]

# =============================================================================
# METADATOS DEL PAQUETE
# =============================================================================

__version__ = '1.0.0'
__author__ = 'Sistema de Zonas de Cobertura'
__description__ = 'Paquete de autenticación con Google OAuth para el Sistema de Zonas de Cobertura'
