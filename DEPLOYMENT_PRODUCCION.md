# 🚀 Guía de Deployment a Producción - Sistema de Zonas de Cobertura

## 📋 Tabla de Contenidos

1. [Requisitos del Sistema](#requisitos-del-sistema)
2. [🪟 DEPLOYMENT EN WINDOWS SERVER](#-deployment-en-windows-server)
3. [🐧 DEPLOYMENT EN LINUX (Ubuntu/CentOS)](#-deployment-en-linux-ubuntucentos)
4. [Preparación del Servidor](#preparación-del-servidor)
5. [Instalación de Dependencias](#instalación-de-dependencias)
6. [Configuración de la Aplicación](#configuración-de-la-aplicación)
7. [Variables de Entorno](#variables-de-entorno)
8. [Configuración del Servidor Web](#configuración-del-servidor-web)
9. [Base de Datos](#base-de-datos)
10. [Configuración de Seguridad](#configuración-de-seguridad)
11. [Proceso de Deployment](#proceso-de-deployment)
12. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
13. [Resolución de Problemas](#resolución-de-problemas)

---

## 🖥️ Requisitos del Sistema

### Para Windows Server
- **Sistema Operativo**: Windows Server 2019/2022 o Windows 10/11 Pro
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Almacenamiento**: 20 GB SSD
- **Red**: Conexión estable a internet

### Para Linux (Ubuntu/CentOS)
- **Sistema Operativo**: Ubuntu 20.04 LTS o superior / CentOS 8+ / RHEL 8+
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Almacenamiento**: 20 GB SSD
- **Red**: Conexión estable a internet

---

## 🪟 DEPLOYMENT EN WINDOWS SERVER

### 1. Preparación del Sistema Windows

#### Instalar Python
```powershell
# Descargar Python desde python.org o usar winget
winget install Python.Python.3.11

# Verificar instalación
python --version
pip --version
```

#### Instalar Git
```powershell
# Usar winget para instalar Git
winget install Git.Git

# O descargar desde git-scm.com
# Verificar instalación
git --version
```

#### Instalar IIS (Opcional - para servir archivos estáticos)
```powershell
# Habilitar IIS
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-WebServer, IIS-CommonHttpFeatures, IIS-HttpErrors, IIS-HttpLogging, IIS-RequestFiltering, IIS-StaticContent, IIS-DefaultDocument, IIS-DirectoryBrowsing

# Instalar URL Rewrite Module
# Descargar desde: https://www.iis.net/downloads/microsoft/url-rewrite
```

### 2. Configuración del Usuario y Directorios

```powershell
# Crear usuario para la aplicación (ejecutar como Administrador)
New-LocalUser -Name "zonasapp" -Description "Usuario para Sistema de Zonas de Cobertura" -NoPassword
Add-LocalGroupMember -Group "Users" -Member "zonasapp"

# Crear directorio de la aplicación
New-Item -ItemType Directory -Path "C:\inetpub\zonas-cobertura" -Force
New-Item -ItemType Directory -Path "C:\inetpub\zonas-cobertura\logs" -Force
New-Item -ItemType Directory -Path "C:\inetpub\zonas-cobertura\uploads" -Force
New-Item -ItemType Directory -Path "C:\inetpub\zonas-cobertura\backups" -Force

# Establecer permisos
icacls "C:\inetpub\zonas-cobertura" /grant zonasapp:(OI)(CI)F /T
```

### 3. Clonar y Configurar la Aplicación

```powershell
# Cambiar al directorio de la aplicación
cd C:\inetpub\zonas-cobertura

# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO> .

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn waitress
```

### 4. Variables de Entorno en Windows

#### Crear archivo .env
```powershell
# Crear archivo .env
New-Item -ItemType File -Path "C:\inetpub\zonas-cobertura\.env" -Force
```

#### Contenido del archivo .env para Windows
```bash
# =============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN - SISTEMA DE ZONAS DE COBERTURA (WINDOWS)
# =============================================================================

# =====================================================================
# CONFIGURACIÓN DE FLASK
# =====================================================================
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=tu_clave_secreta_muy_segura_aqui_cambiar_por_una_real

# =====================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================================
DATABASE_PATH=C:\inetpub\zonas-cobertura\zonas_cobertura.db

# =====================================================================
# CONFIGURACIÓN DE API EXTERNA
# =====================================================================
EXTERNAL_API_BASE_URL=https://tu-api-externa.com
EXTERNAL_API_TOKEN=tu_token_de_api_externa_aqui
EXTERNAL_API_TIMEOUT=30

# =====================================================================
# CONFIGURACIÓN DE GEOCODIFICACIÓN
# =====================================================================
GEOCODING_SERVICE=nominatim
NOMINATIM_USER_AGENT=zonas_cobertura_production

# =====================================================================
# CONFIGURACIÓN DE MAPAS
# =====================================================================
DEFAULT_MAP_CENTER_LAT=-34.6037
DEFAULT_MAP_CENTER_LNG=-58.3816
DEFAULT_MAP_ZOOM=12

# =====================================================================
# CONFIGURACIÓN DE LÍMITES
# =====================================================================
MAX_POLYGON_POINTS=100
MAX_ZONES_PER_BRANCH=10
MAX_CONTENT_LENGTH=16777216

# =====================================================================
# CONFIGURACIÓN DE LOGGING
# =====================================================================
LOG_LEVEL=INFO
LOG_FILE=C:\inetpub\zonas-cobertura\logs\app.log

# =====================================================================
# CONFIGURACIÓN DE ARCHIVOS
# =====================================================================
UPLOAD_FOLDER=C:\inetpub\zonas-cobertura\uploads

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =====================================================================
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### 5. Configuración de Waitress (Servidor WSGI para Windows)

#### Crear archivo waitress_server.py
```python
# waitress_server.py
import os
from waitress import serve
from app import app

if __name__ == '__main__':
    # Configuración para producción
    serve(
        app,
        host='127.0.0.1',
        port=8000,
        threads=4,
        connection_limit=1000,
        cleanup_interval=30,
        channel_timeout=120,
        log_socket_errors=True
    )
```

### 6. Configuración como Servicio de Windows

#### Crear archivo install_service.py
```python
# install_service.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import subprocess
import time

class ZonasCoberturaService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZonasCoberturaService"
    _svc_display_name_ = "Sistema de Zonas de Cobertura"
    _svc_description_ = "Servicio web para gestión de zonas de cobertura de delivery"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        # Cambiar al directorio de la aplicación
        os.chdir(r'C:\inetpub\zonas-cobertura')
        
        # Activar entorno virtual y ejecutar aplicación
        python_path = r'C:\inetpub\zonas-cobertura\venv\Scripts\python.exe'
        script_path = r'C:\inetpub\zonas-cobertura\waitress_server.py'
        
        while self.is_alive:
            try:
                # Ejecutar la aplicación
                process = subprocess.Popen([python_path, script_path])
                process.wait()
                
                if not self.is_alive:
                    break
                    
                # Si el proceso termina inesperadamente, esperar antes de reiniciar
                time.sleep(5)
                
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error en el servicio: {str(e)}")
                time.sleep(10)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ZonasCoberturaService)
```

#### Instalar dependencias para el servicio
```powershell
# Instalar pywin32 para servicios de Windows
pip install pywin32

# Instalar el servicio
python install_service.py install

# Iniciar el servicio
python install_service.py start

# Verificar estado del servicio
sc query ZonasCoberturaService
```

### 7. Configuración de IIS como Proxy Reverso

#### Instalar URL Rewrite Module
```powershell
# Descargar e instalar URL Rewrite Module desde:
# https://www.iis.net/downloads/microsoft/url-rewrite
```

#### Crear archivo web.config
```xml
<!-- web.config para IIS -->
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxyInboundRule1" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://127.0.0.1:8000/{R:1}" />
                </rule>
            </rules>
        </rewrite>
        <security>
            <requestFiltering>
                <requestLimits maxAllowedContentLength="16777216" />
            </requestFiltering>
        </security>
        <httpProtocol>
            <customHeaders>
                <add name="X-Frame-Options" value="DENY" />
                <add name="X-Content-Type-Options" value="nosniff" />
                <add name="X-XSS-Protection" value="1; mode=block" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
```

### 8. Configuración de Firewall de Windows

```powershell
# Abrir puertos necesarios
New-NetFirewallRule -DisplayName "Zonas Cobertura HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "Zonas Cobertura HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
New-NetFirewallRule -DisplayName "Zonas Cobertura App" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Verificar reglas
Get-NetFirewallRule -DisplayName "*Zonas*"
```

### 9. Scripts de Deployment para Windows

#### Script de Deployment (deploy.ps1)
```powershell
# deploy.ps1
param(
    [string]$Environment = "production"
)

Write-Host "🚀 Iniciando deployment en Windows..." -ForegroundColor Green

# Configurar variables
$AppDir = "C:\inetpub\zonas-cobertura"
$BackupDir = "C:\inetpub\zonas-cobertura\backups"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"

try {
    # 1. Crear backup
    Write-Host "📦 Creando backup..." -ForegroundColor Yellow
    if (Test-Path "$AppDir\zonas_cobertura.db") {
        Copy-Item "$AppDir\zonas_cobertura.db" "$BackupDir\zonas_cobertura_backup_$Date.db"
    }

    # 2. Cambiar al directorio de la aplicación
    Set-Location $AppDir

    # 3. Activar entorno virtual
    Write-Host "🐍 Activando entorno virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"

    # 4. Actualizar código
    Write-Host "📥 Actualizando código..." -ForegroundColor Yellow
    git pull origin main

    # 5. Instalar dependencias
    Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt

    # 6. Inicializar base de datos
    Write-Host "🗄️ Verificando base de datos..." -ForegroundColor Yellow
    python -c "from app import init_db; init_db()"

    # 7. Reiniciar servicio
    Write-Host "🔄 Reiniciando servicio..." -ForegroundColor Yellow
    Restart-Service -Name "ZonasCoberturaService" -Force

    # 8. Verificar aplicación
    Write-Host "✅ Verificando aplicación..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Aplicación funcionando correctamente" -ForegroundColor Green
    } else {
        throw "La aplicación no responde correctamente"
    }

    Write-Host "🎉 Deployment completado exitosamente!" -ForegroundColor Green

} catch {
    Write-Host "❌ Error durante el deployment: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
```

#### Script de Backup (backup.ps1)
```powershell
# backup.ps1
$AppDir = "C:\inetpub\zonas-cobertura"
$BackupDir = "C:\inetpub\zonas-cobertura\backups"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "📦 Iniciando backup..." -ForegroundColor Green

# Crear directorio de backup si no existe
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force
}

# Backup de base de datos
if (Test-Path "$AppDir\zonas_cobertura.db") {
    Copy-Item "$AppDir\zonas_cobertura.db" "$BackupDir\zonas_cobertura_$Date.db"
    Write-Host "✅ Base de datos respaldada" -ForegroundColor Green
}

# Backup de archivos de configuración
$configFiles = @(".env", "waitress_server.py", "install_service.py")
foreach ($file in $configFiles) {
    if (Test-Path "$AppDir\$file") {
        Copy-Item "$AppDir\$file" "$BackupDir\${file}_$Date"
    }
}

# Backup de uploads
if (Test-Path "$AppDir\uploads") {
    Compress-Archive -Path "$AppDir\uploads\*" -DestinationPath "$BackupDir\uploads_$Date.zip" -Force
    Write-Host "✅ Archivos de upload respaldados" -ForegroundColor Green
}

# Limpiar backups antiguos (mantener últimos 30 días)
Get-ChildItem -Path $BackupDir -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force

Write-Host "🎉 Backup completado: $Date" -ForegroundColor Green
```

### 10. Configuración de Tareas Programadas

```powershell
# Crear tarea programada para backup diario
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\inetpub\zonas-cobertura\backup.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "ZonasCoberturaBackup" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Backup diario del Sistema de Zonas de Cobertura"
```

### 11. Monitoreo en Windows

#### Script de Monitoreo (monitor.ps1)
```powershell
# monitor.ps1
Write-Host "=== Estado del Sistema ===" -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date)" -ForegroundColor White
Write-Host "Uptime: $((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime)" -ForegroundColor White
Write-Host ""

Write-Host "=== Uso de Memoria ===" -ForegroundColor Cyan
Get-Counter '\Memory\Available MBytes' | Select-Object -ExpandProperty CounterSamples | ForEach-Object { 
    $total = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1MB
    $available = $_.CookedValue
    $used = $total - $available
    Write-Host "Total: $([math]::Round($total, 2)) MB" -ForegroundColor White
    Write-Host "Usado: $([math]::Round($used, 2)) MB" -ForegroundColor White
    Write-Host "Disponible: $([math]::Round($available, 2)) MB" -ForegroundColor White
}
Write-Host ""

Write-Host "=== Uso de Disco ===" -ForegroundColor Cyan
Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } | ForEach-Object {
    $size = [math]::Round($_.Size / 1GB, 2)
    $free = [math]::Round($_.FreeSpace / 1GB, 2)
    $used = $size - $free
    Write-Host "$($_.DeviceID) - Total: $size GB, Usado: $used GB, Libre: $free GB" -ForegroundColor White
}
Write-Host ""

Write-Host "=== Estado de Servicios ===" -ForegroundColor Cyan
$services = @("W3SVC", "ZonasCoberturaService")
foreach ($service in $services) {
    $status = Get-Service -Name $service -ErrorAction SilentlyContinue
    if ($status) {
        Write-Host "$service : $($status.Status)" -ForegroundColor White
    }
}
Write-Host ""

Write-Host "=== Conexiones de Red ===" -ForegroundColor Cyan
netstat -an | Select-String ":80|:443|:8000" | ForEach-Object { Write-Host $_.Line -ForegroundColor White }
```

### 12. Comandos de Mantenimiento en Windows

```powershell
# Ver logs de la aplicación
Get-Content "C:\inetpub\zonas-cobertura\logs\app.log" -Tail 50 -Wait

# Ver estado del servicio
Get-Service -Name "ZonasCoberturaService"

# Reiniciar servicio
Restart-Service -Name "ZonasCoberturaService"

# Ver logs del servicio
Get-EventLog -LogName Application -Source "ZonasCoberturaService" -Newest 10

# Verificar conectividad
Test-NetConnection -ComputerName 127.0.0.1 -Port 8000

# Verificar API externa
$headers = @{ "Authorization" = "Bearer $env:EXTERNAL_API_TOKEN" }
Invoke-RestMethod -Uri "$env:EXTERNAL_API_BASE_URL/internalapi/SubsidiaryList/1" -Headers $headers
```

### 13. Resolución de Problemas en Windows

#### Problemas Comunes
```powershell
# Error: "Service cannot be started"
# Verificar permisos del usuario del servicio
icacls "C:\inetpub\zonas-cobertura" /grant zonasapp:(OI)(CI)F /T

# Error: "Port already in use"
# Verificar qué proceso usa el puerto
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Error: "Module not found"
# Verificar entorno virtual
& "C:\inetpub\zonas-cobertura\venv\Scripts\Activate.ps1"
pip list

# Error: "Permission denied"
# Ejecutar PowerShell como Administrador
Start-Process PowerShell -Verb RunAs
```

---

## 🐧 DEPLOYMENT EN LINUX (Ubuntu/CentOS)

### Hardware Mínimo Recomendado
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Almacenamiento**: 20 GB SSD
- **Red**: Conexión estable a internet

### Software Requerido
- **Sistema Operativo**: Ubuntu 20.04 LTS o superior / CentOS 8+ / RHEL 8+
- **Python**: 3.8 o superior
- **Nginx**: 1.18 o superior
- **PostgreSQL**: 12 o superior (opcional, para reemplazar SQLite)
- **Git**: Para clonar el repositorio

---

## 🛠️ Preparación del Servidor

### 1. Actualizar el Sistema

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
# o para versiones más nuevas
sudo dnf update -y
```

### 2. Instalar Herramientas Básicas

```bash
# Ubuntu/Debian
sudo apt install -y curl wget git vim htop unzip

# CentOS/RHEL
sudo yum install -y curl wget git vim htop unzip
```

### 3. Crear Usuario para la Aplicación

```bash
# Crear usuario dedicado para la aplicación
sudo useradd -m -s /bin/bash zonasapp
sudo usermod -aG sudo zonasapp

# Cambiar al usuario de la aplicación
sudo su - zonasapp
```

---

## 📦 Instalación de Dependencias

### 1. Instalar Python y pip

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv python3-dev

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-venv python3-devel
```

### 2. Instalar Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx

# Habilitar y iniciar Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 3. Instalar PostgreSQL (Opcional)

```bash
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install -y postgresql-server postgresql-contrib

# Inicializar base de datos (solo en CentOS/RHEL)
sudo postgresql-setup initdb

# Habilitar y iniciar PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 4. Instalar Gunicorn y Supervisor

```bash
# Instalar Gunicorn (servidor WSGI para producción)
pip3 install gunicorn

# Instalar Supervisor para gestión de procesos
sudo apt install -y supervisor  # Ubuntu/Debian
sudo yum install -y supervisor  # CentOS/RHEL
```

---

## ⚙️ Configuración de la Aplicación

### 1. Clonar el Repositorio

```bash
# Cambiar al directorio home del usuario
cd /home/zonasapp

# Clonar el repositorio
git clone <URL_DEL_REPOSITORIO> zonas-cobertura
cd zonas-cobertura
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip
```

### 3. Instalar Dependencias de Python

```bash
# Instalar dependencias desde requirements.txt
pip install -r requirements.txt

# Instalar dependencias adicionales para producción
pip install gunicorn psycopg2-binary  # psycopg2-binary solo si usas PostgreSQL
```

### 4. Crear Estructura de Directorios

```bash
# Crear directorios necesarios
mkdir -p logs
mkdir -p uploads
mkdir -p backups

# Establecer permisos
chmod 755 logs uploads backups
```

---

## 🔧 Variables de Entorno

### 1. Crear Archivo de Variables de Entorno

```bash
# Crear archivo .env en el directorio raíz
nano .env
```

### 2. Configurar Variables de Entorno

```bash
# =============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN - SISTEMA DE ZONAS DE COBERTURA
# =============================================================================

# =====================================================================
# CONFIGURACIÓN DE FLASK
# =====================================================================
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=tu_clave_secreta_muy_segura_aqui_cambiar_por_una_real

# =====================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================================
# Para SQLite (por defecto)
DATABASE_PATH=/home/zonasapp/zonas-cobertura/zonas_cobertura.db

# Para PostgreSQL (opcional)
# DATABASE_URL=postgresql://usuario:password@localhost:5432/zonas_cobertura

# =====================================================================
# CONFIGURACIÓN DE API EXTERNA
# =====================================================================
EXTERNAL_API_BASE_URL=https://tu-api-externa.com
EXTERNAL_API_TOKEN=tu_token_de_api_externa_aqui
EXTERNAL_API_TIMEOUT=30

# =====================================================================
# CONFIGURACIÓN DE GEOCODIFICACIÓN
# =====================================================================
GEOCODING_SERVICE=nominatim
NOMINATIM_USER_AGENT=zonas_cobertura_production

# =====================================================================
# CONFIGURACIÓN DE MAPAS
# =====================================================================
DEFAULT_MAP_CENTER_LAT=-34.6037
DEFAULT_MAP_CENTER_LNG=-58.3816
DEFAULT_MAP_ZOOM=12

# =====================================================================
# CONFIGURACIÓN DE LÍMITES
# =====================================================================
MAX_POLYGON_POINTS=100
MAX_ZONES_PER_BRANCH=10
MAX_CONTENT_LENGTH=16777216

# =====================================================================
# CONFIGURACIÓN DE LOGGING
# =====================================================================
LOG_LEVEL=INFO
LOG_FILE=/home/zonasapp/zonas-cobertura/logs/app.log

# =====================================================================
# CONFIGURACIÓN DE ARCHIVOS
# =====================================================================
UPLOAD_FOLDER=/home/zonasapp/zonas-cobertura/uploads

# =====================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =====================================================================
# Configuración de CORS (ajustar según necesidades)
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# Configuración de rate limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### 3. Establecer Permisos de Seguridad

```bash
# Establecer permisos restrictivos para el archivo .env
chmod 600 .env

# Cambiar propietario
sudo chown zonasapp:zonasapp .env
```

---

## 🌐 Configuración del Servidor Web

### 1. Configurar Gunicorn

```bash
# Crear archivo de configuración de Gunicorn
nano gunicorn.conf.py
```

```python
# gunicorn.conf.py
import multiprocessing
import os

# Configuración de Gunicorn para producción
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Configuración de logging
accesslog = "/home/zonasapp/zonas-cobertura/logs/gunicorn_access.log"
errorlog = "/home/zonasapp/zonas-cobertura/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configuración de usuario
user = "zonasapp"
group = "zonasapp"

# Configuración de proceso
daemon = False
pidfile = "/home/zonasapp/zonas-cobertura/gunicorn.pid"
```

### 2. Configurar Supervisor

```bash
# Crear archivo de configuración de Supervisor
sudo nano /etc/supervisor/conf.d/zonas-cobertura.conf
```

```ini
[program:zonas-cobertura]
command=/home/zonasapp/zonas-cobertura/venv/bin/gunicorn --config gunicorn.conf.py app:app
directory=/home/zonasapp/zonas-cobertura
user=zonasapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/zonasapp/zonas-cobertura/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/zonasapp/zonas-cobertura/venv/bin"
```

### 3. Configurar Nginx

```bash
# Crear archivo de configuración de Nginx
sudo nano /etc/nginx/sites-available/zonas-cobertura
```

```nginx
# /etc/nginx/sites-available/zonas-cobertura
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirección a HTTPS (recomendado para producción)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    # Configuración SSL (ajustar rutas según certificados)
    ssl_certificate /etc/ssl/certs/zonas-cobertura.crt;
    ssl_certificate_key /etc/ssl/private/zonas-cobertura.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Configuración de seguridad
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Configuración de archivos estáticos
    location /static/ {
        alias /home/zonasapp/zonas-cobertura/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Configuración de uploads
    location /uploads/ {
        alias /home/zonasapp/zonas-cobertura/uploads/;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Proxy a la aplicación Flask
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Configuración de logs
    access_log /var/log/nginx/zonas-cobertura_access.log;
    error_log /var/log/nginx/zonas-cobertura_error.log;
}
```

### 4. Habilitar el Sitio

```bash
# Habilitar el sitio en Nginx
sudo ln -s /etc/nginx/sites-available/zonas-cobertura /etc/nginx/sites-enabled/

# Verificar configuración de Nginx
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

---

## 🗄️ Base de Datos

### 1. Configuración de SQLite (Por Defecto)

```bash
# La base de datos SQLite se crea automáticamente
# Solo asegurar permisos correctos
sudo chown zonasapp:zonasapp /home/zonasapp/zonas-cobertura/zonas_cobertura.db
chmod 664 /home/zonasapp/zonas-cobertura/zonas_cobertura.db
```

### 2. Configuración de PostgreSQL (Opcional)

```bash
# Conectar a PostgreSQL como usuario postgres
sudo -u postgres psql

# Crear base de datos y usuario
CREATE DATABASE zonas_cobertura;
CREATE USER zonasapp WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE zonas_cobertura TO zonasapp;
\q

# Actualizar variables de entorno
echo "DATABASE_URL=postgresql://zonasapp:tu_password_seguro@localhost:5432/zonas_cobertura" >> .env
```

---

## 🔒 Configuración de Seguridad

### 1. Configurar Firewall

```bash
# Ubuntu/Debian (UFW)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# CentOS/RHEL (firewalld)
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. Configurar SSL/TLS

```bash
# Instalar Certbot para Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu/Debian
sudo yum install -y certbot python3-certbot-nginx  # CentOS/RHEL

# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Configurar renovación automática
sudo crontab -e
# Agregar línea:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Configurar Backup Automático

```bash
# Crear script de backup
nano /home/zonasapp/backup.sh
```

```bash
#!/bin/bash
# Script de backup para Sistema de Zonas de Cobertura

BACKUP_DIR="/home/zonasapp/backups"
APP_DIR="/home/zonasapp/zonas-cobertura"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backup si no existe
mkdir -p $BACKUP_DIR

# Backup de la base de datos
if [ -f "$APP_DIR/zonas_cobertura.db" ]; then
    cp "$APP_DIR/zonas_cobertura.db" "$BACKUP_DIR/zonas_cobertura_$DATE.db"
fi

# Backup de archivos de configuración
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C "$APP_DIR" .env gunicorn.conf.py

# Backup de uploads
if [ -d "$APP_DIR/uploads" ]; then
    tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$APP_DIR" uploads/
fi

# Limpiar backups antiguos (mantener últimos 30 días)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completado: $DATE"
```

```bash
# Hacer ejecutable el script
chmod +x /home/zonasapp/backup.sh

# Configurar cron para backup diario
crontab -e
# Agregar línea:
# 0 2 * * * /home/zonasapp/backup.sh >> /home/zonasapp/backup.log 2>&1
```

---

## 🚀 Proceso de Deployment

### 1. Script de Deployment

```bash
# Crear script de deployment
nano /home/zonasapp/deploy.sh
```

```bash
#!/bin/bash
# Script de deployment para Sistema de Zonas de Cobertura

set -e  # Salir si hay algún error

APP_DIR="/home/zonasapp/zonas-cobertura"
BACKUP_DIR="/home/zonasapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🚀 Iniciando deployment..."

# 1. Crear backup antes del deployment
echo "📦 Creando backup..."
mkdir -p $BACKUP_DIR
if [ -f "$APP_DIR/zonas_cobertura.db" ]; then
    cp "$APP_DIR/zonas_cobertura.db" "$BACKUP_DIR/zonas_cobertura_backup_$DATE.db"
fi

# 2. Activar entorno virtual
echo "🐍 Activando entorno virtual..."
cd $APP_DIR
source venv/bin/activate

# 3. Actualizar código desde repositorio
echo "📥 Actualizando código..."
git pull origin main

# 4. Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# 5. Ejecutar migraciones de base de datos (si las hay)
echo "🗄️ Verificando base de datos..."
python -c "from app import init_db; init_db()"

# 6. Recargar aplicación
echo "🔄 Recargando aplicación..."
sudo supervisorctl restart zonas-cobertura

# 7. Verificar que la aplicación esté funcionando
echo "✅ Verificando aplicación..."
sleep 5
if curl -f http://127.0.0.1:8000/ > /dev/null 2>&1; then
    echo "✅ Aplicación funcionando correctamente"
else
    echo "❌ Error: La aplicación no responde"
    exit 1
fi

echo "🎉 Deployment completado exitosamente!"
```

```bash
# Hacer ejecutable el script
chmod +x /home/zonasapp/deploy.sh
```

### 2. Comandos de Deployment

```bash
# Deployment manual
cd /home/zonasapp/zonas-cobertura
./deploy.sh

# O paso a paso:
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
sudo supervisorctl restart zonas-cobertura
```

---

## 📊 Monitoreo y Mantenimiento

### 1. Configurar Logs

```bash
# Configurar rotación de logs
sudo nano /etc/logrotate.d/zonas-cobertura
```

```
/home/zonasapp/zonas-cobertura/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 zonasapp zonasapp
    postrotate
        sudo supervisorctl restart zonas-cobertura
    endscript
}
```

### 2. Monitoreo de Sistema

```bash
# Instalar herramientas de monitoreo
sudo apt install -y htop iotop nethogs  # Ubuntu/Debian
sudo yum install -y htop iotop nethogs  # CentOS/RHEL

# Script de monitoreo
nano /home/zonasapp/monitor.sh
```

```bash
#!/bin/bash
# Script de monitoreo básico

echo "=== Estado del Sistema ==="
echo "Fecha: $(date)"
echo "Uptime: $(uptime)"
echo ""

echo "=== Uso de Memoria ==="
free -h
echo ""

echo "=== Uso de Disco ==="
df -h
echo ""

echo "=== Estado de Servicios ==="
systemctl is-active nginx
systemctl is-active supervisor
echo ""

echo "=== Estado de la Aplicación ==="
sudo supervisorctl status zonas-cobertura
echo ""

echo "=== Conexiones de Red ==="
netstat -tulpn | grep :80
netstat -tulpn | grep :443
netstat -tulpn | grep :8000
```

### 3. Comandos de Mantenimiento

```bash
# Ver logs de la aplicación
tail -f /home/zonasapp/zonas-cobertura/logs/app.log

# Ver logs de Gunicorn
tail -f /home/zonasapp/zonas-cobertura/logs/gunicorn_error.log

# Ver logs de Nginx
sudo tail -f /var/log/nginx/zonas-cobertura_error.log

# Reiniciar servicios
sudo systemctl restart nginx
sudo supervisorctl restart zonas-cobertura

# Verificar estado de servicios
sudo systemctl status nginx
sudo supervisorctl status zonas-cobertura

# Verificar configuración
sudo nginx -t
```

---

## 🔧 Resolución de Problemas

### 1. Problemas Comunes

#### Error: "Permission denied"
```bash
# Verificar permisos
sudo chown -R zonasapp:zonasapp /home/zonasapp/zonas-cobertura
chmod +x /home/zonasapp/zonas-cobertura/venv/bin/gunicorn
```

#### Error: "Port already in use"
```bash
# Verificar qué proceso usa el puerto
sudo netstat -tulpn | grep :8000
sudo lsof -i :8000

# Matar proceso si es necesario
sudo kill -9 <PID>
```

#### Error: "Module not found"
```bash
# Verificar entorno virtual
source /home/zonasapp/zonas-cobertura/venv/bin/activate
pip list

# Reinstalar dependencias
pip install -r requirements.txt
```

### 2. Comandos de Diagnóstico

```bash
# Verificar conectividad de API externa
curl -H "Authorization: Bearer $EXTERNAL_API_TOKEN" $EXTERNAL_API_BASE_URL/internalapi/SubsidiaryList/1

# Verificar base de datos
sqlite3 /home/zonasapp/zonas-cobertura/zonas_cobertura.db ".tables"

# Verificar configuración de Nginx
sudo nginx -t

# Verificar configuración de Supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

### 3. Logs de Debug

```bash
# Habilitar logs detallados temporalmente
export FLASK_DEBUG=True
export LOG_LEVEL=DEBUG

# Reiniciar aplicación
sudo supervisorctl restart zonas-cobertura

# Ver logs en tiempo real
tail -f /home/zonasapp/zonas-cobertura/logs/app.log
```

---

## 📋 Checklist de Deployment

### Pre-Deployment
- [ ] Servidor configurado con requisitos mínimos
- [ ] Usuario de aplicación creado
- [ ] Dependencias del sistema instaladas
- [ ] Repositorio clonado
- [ ] Entorno virtual creado y activado

### Configuración
- [ ] Variables de entorno configuradas
- [ ] Archivo .env creado con permisos correctos
- [ ] Base de datos configurada
- [ ] Gunicorn configurado
- [ ] Supervisor configurado
- [ ] Nginx configurado

### Seguridad
- [ ] Firewall configurado
- [ ] SSL/TLS configurado
- [ ] Permisos de archivos correctos
- [ ] Backup automático configurado

### Deployment
- [ ] Aplicación desplegada
- [ ] Servicios iniciados
- [ ] Aplicación respondiendo
- [ ] Logs funcionando
- [ ] Monitoreo configurado

### Post-Deployment
- [ ] Pruebas de funcionalidad realizadas
- [ ] Monitoreo activo
- [ ] Documentación actualizada
- [ ] Equipo notificado

---

## 📞 Soporte y Contacto

Para soporte técnico o reportar problemas:

1. **Revisar logs**: Verificar logs de aplicación, Nginx y Supervisor
2. **Verificar estado**: Comprobar estado de servicios y conectividad
3. **Documentar**: Registrar pasos realizados y mensajes de error
4. **Contactar**: Equipo de desarrollo con información detallada

---

## 📚 Recursos Adicionales

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de Gunicorn](https://gunicorn.org/)
- [Documentación de Nginx](https://nginx.org/en/docs/)
- [Documentación de Supervisor](http://supervisord.org/)
- [Guía de Seguridad de Ubuntu](https://ubuntu.com/security)

---

**Nota**: Este documento debe ser actualizado según las necesidades específicas del entorno de producción y las políticas de seguridad de la organización.
