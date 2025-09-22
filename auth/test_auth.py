#!/usr/bin/env python3
"""
Script de prueba para diagnosticar el problema de autenticación
"""

import requests
import json
from urllib.parse import urlencode

def test_auth_flow():
    """Prueba el flujo de autenticación paso a paso"""
    
    base_url = "http://localhost:5000"
    
    print("=== PRUEBA DE FLUJO DE AUTENTICACIÓN ===")
    
    # 1. Probar el endpoint de login
    print("\n1. Probando endpoint de login...")
    try:
        response = requests.get(f"{base_url}/auth/login", allow_redirects=False)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code in [301, 302]:
            print(f"Redirect URL: {response.headers.get('Location')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Probar el endpoint de status
    print("\n2. Probando endpoint de status...")
    try:
        response = requests.get(f"{base_url}/auth/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Probar el endpoint principal
    print("\n3. Probando endpoint principal...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Simular callback con parámetros de prueba
    print("\n4. Simulando callback con parámetros de prueba...")
    test_params = {
        'code': 'test_code_123',
        'state': 'test_state_456',
        'scope': 'email profile',
        'authuser': '0'
    }
    
    try:
        response = requests.get(f"{base_url}/auth/callback", params=test_params, allow_redirects=False)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code in [301, 302]:
            print(f"Redirect URL: {response.headers.get('Location')}")
        print(f"Response body: {response.text[:500]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_auth_flow()
