import { useState } from 'react'
import { 
  Server, Shield, Mail, Send, FileCode, Settings, 
  Terminal, Copy, Check, ChevronRight, AlertTriangle,
  CheckCircle, Clock, Lock, Globe, Database, Zap,
  BookOpen, Download, Eye
} from 'lucide-react'

type Tab = 'overview' | 'credentials' | 'docker' | 'security' | 'email' | 'telegram' | 'files'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [copiedFile, setCopiedFile] = useState<string | null>(null)
  const [expandedFile, setExpandedFile] = useState<string | null>(null)

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedFile(id)
    setTimeout(() => setCopiedFile(null), 2000)
  }

  const tabs = [
    { id: 'overview' as Tab, label: 'Resumen', icon: Eye },
    { id: 'credentials' as Tab, label: '⚠️ Credenciales', icon: Lock },
    { id: 'docker' as Tab, label: 'Docker', icon: Server },
    { id: 'security' as Tab, label: 'Seguridad', icon: Shield },
    { id: 'email' as Tab, label: 'Email Reportes', icon: Mail },
    { id: 'telegram' as Tab, label: 'Telegram Bot', icon: Send },
    { id: 'files' as Tab, label: 'Archivos', icon: FileCode },
  ]

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Panel de Administración</h1>
              <p className="text-sm text-gray-400">Dashboard de Licitaciones - Comprar.gob.ar</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-green-400 text-sm">
              <CheckCircle className="w-4 h-4" />
              Sistema Activo
            </span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row">
        {/* Sidebar */}
        <nav className="lg:w-64 bg-gray-800 border-r border-gray-700 p-4">
          <ul className="space-y-1">
            {tabs.map(tab => (
              <li key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-all ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              </li>
            ))}
          </ul>
          
          <div className="mt-8 p-4 bg-gray-700/50 rounded-lg border border-gray-600">
            <h3 className="text-sm font-semibold text-gray-300 mb-2">Repositorio Original</h3>
            <a 
              href="https://github.com/ematevez/comprar" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-400 text-sm hover:underline break-all"
            >
              github.com/ematevez/comprar
            </a>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6 overflow-auto">
          {activeTab === 'overview' && <OverviewSection />}
          {activeTab === 'credentials' && <CredentialsSection copiedFile={copiedFile} copyToClipboard={copyToClipboard} />}
          {activeTab === 'docker' && <DockerSection copiedFile={copiedFile} copyToClipboard={copyToClipboard} />}
          {activeTab === 'security' && <SecuritySection copiedFile={copiedFile} copyToClipboard={copyToClipboard} />}
          {activeTab === 'email' && <EmailSection copiedFile={copiedFile} copyToClipboard={copyToClipboard} />}
          {activeTab === 'telegram' && <TelegramSection copiedFile={copiedFile} copyToClipboard={copyToClipboard} />}
          {activeTab === 'files' && <FilesSection expandedFile={expandedFile} setExpandedFile={setExpandedFile} copiedFile={copiedFile} copyToClipboard={copyToClipboard} />}
        </main>
      </div>
    </div>
  )
}

// ==================== OVERVIEW ====================
function OverviewSection() {
  const features = [
    { icon: Server, title: 'Dockerización', desc: 'Contenedores con Docker Compose para despliegue fácil', color: 'bg-blue-500' },
    { icon: Shield, title: 'Seguridad', desc: 'HTTPS, autenticación, rate limiting, firewall', color: 'bg-red-500' },
    { icon: Mail, title: 'Reportes Email', desc: 'Reporte diario automático a correos configurables', color: 'bg-green-500' },
    { icon: Send, title: 'Telegram Bot', desc: 'Bot interactivo para monitoreo y control remoto', color: 'bg-purple-500' },
    { icon: Globe, title: 'Acceso Red', desc: 'Servidor accesible desde toda la red local/externa', color: 'bg-yellow-500' },
    { icon: Zap, title: 'Auto-scheduler', desc: 'Ejecución programada automática de scraping', color: 'bg-orange-500' },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Resumen del Proyecto</h2>
      <p className="text-gray-400 mb-6">
        Este panel te guía paso a paso para convertir tu script de Python en un servidor 
        dockerizado, seguro, con reportes por email y bot de Telegram.
      </p>

      {/* Architecture Diagram */}
      <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          Arquitectura Propuesta
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 rounded-lg p-4 text-center border border-gray-600">
            <Globe className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
            <p className="font-semibold text-sm">Nginx (Reverse Proxy)</p>
            <p className="text-xs text-gray-400 mt-1">Puerto 80/443</p>
            <p className="text-xs text-gray-500">SSL + Auth</p>
          </div>
          <div className="bg-gray-700 rounded-lg p-4 text-center border border-gray-600">
            <Server className="w-8 h-8 mx-auto mb-2 text-blue-400" />
            <p className="font-semibold text-sm">App Python</p>
            <p className="text-xs text-gray-400 mt-1">Dashboard + API</p>
            <p className="text-xs text-gray-500">Puerto 8765</p>
          </div>
          <div className="bg-gray-700 rounded-lg p-4 text-center border border-gray-600">
            <Send className="w-8 h-8 mx-auto mb-2 text-purple-400" />
            <p className="font-semibold text-sm">Telegram Bot</p>
            <p className="text-xs text-gray-400 mt-1">Comandos remotos</p>
            <p className="text-xs text-gray-500">Polling/Webhook</p>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-center gap-2 text-gray-500 text-sm">
          <Database className="w-4 h-4" />
          <span>Volumen persistente: Excel, JSON, Logs, PDFs</span>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {features.map((f, i) => (
          <div key={i} className="bg-gray-800 rounded-xl p-5 border border-gray-700 hover:border-gray-500 transition-all">
            <div className={`${f.color} w-10 h-10 rounded-lg flex items-center justify-center mb-3`}>
              <f.icon className="w-5 h-5 text-white" />
            </div>
            <h3 className="font-semibold mb-1">{f.title}</h3>
            <p className="text-sm text-gray-400">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Quick Start */}
      <div className="mt-8 bg-gradient-to-r from-blue-900/50 to-purple-900/50 rounded-xl p-6 border border-blue-700/50">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          Inicio Rápido
        </h3>
        <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm mb-4">
          <p className="text-green-400"># 1. Clonar el repo original</p>
          <p className="text-gray-300">git clone https://github.com/ematevez/comprar.git</p>
          <p className="text-gray-300">cd comprar</p>
          <p className="text-green-400 mt-2"># 2. Copiar los archivos descargables (pestaña "Archivos")</p>
          <p className="text-gray-300"># Los archivos están en /public/archivos/ del workspace</p>
          <p className="text-gray-300">cp docker-compose.yml .</p>
          <p className="text-gray-300">cp Dockerfile .</p>
          <p className="text-gray-300">cp .env.example .env</p>
          <p className="text-green-400 mt-2"># 3. Configurar variables de entorno</p>
          <p className="text-gray-300">nano .env</p>
          <p className="text-green-400 mt-2"># 4. Levantar todo</p>
          <p className="text-gray-300">docker compose up -d</p>
          <p className="text-green-400 mt-2"># 5. Acceder</p>
          <p className="text-gray-300">http://TU_IP:8765</p>
        </div>
        <div className="bg-yellow-900/40 border border-yellow-600 rounded-lg p-3">
          <p className="text-sm text-yellow-200">
            <strong>📥 ¿Dónde están los archivos?</strong> Todos los archivos .py modificados están en la carpeta{' '}
            <code className="bg-gray-800 px-1 rounded">/public/archivos/</code> del workspace. 
            Andá a la pestaña <strong>"Archivos"</strong> para verlos y descargarlos.
          </p>
        </div>
      </div>
    </div>
  )
}

// ==================== CREDENTIALS SECTION ====================
function CredentialsSection({ copiedFile, copyToClipboard }: { copiedFile: string | null; copyToClipboard: (t: string, id: string) => void }) {
  
  const comprarPatched = `"""
comprar.py - VERSIÓN SEGURA (sin credenciales hardcodeadas)
Las credenciales se cargan desde variables de entorno.
"""
import os
import sys
import json
import logging
import threading
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================
# CREDENCIALES - Ahora desde variables de entorno
# ============================================================
CUIT = os.environ.get("CUIT")
PASSWORD = os.environ.get("PASSWORD")

if not CUIT or not PASSWORD:
    print("❌ ERROR: Faltan variables de entorno CUIT y/o PASSWORD")
    print("   Configurá tu archivo .env (ver .env.example)")
    sys.exit(1)

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================
LOG_FILE = "logs_comprar.txt"

logger = logging.getLogger("comprar")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
file_handler.setFormatter(file_fmt)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_fmt = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_fmt)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ... (el resto del código queda igual) ...

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    # Las credenciales YA están cargadas arriba desde os.environ
    
    INTERVALO_MINIMO_HORAS = int(os.environ.get("INTERVALO_HORAS", "24"))
    TIMEOUT_INACTIVIDAD = int(os.environ.get("TIMEOUT_INACTIVIDAD", "60"))
    
    hoy = datetime.now()
    hace_un_mes = hoy - timedelta(days=30)
    fecha_desde = hace_un_mes.strftime("%d/%m/%Y")
    fecha_hasta = hoy.strftime("%d/%m/%Y")
    
    log_info(f"📅 Período de búsqueda: {fecha_desde} a {fecha_hasta}")
    log_info(f"⏱️ Timeout de inactividad: {TIMEOUT_INACTIVIDAD}s")
    log_info(f"🔐 Credenciales cargadas desde variables de entorno ✅")
    
    login_comprar_y_extraer(
        CUIT, 
        PASSWORD, 
        fecha_desde=fecha_desde, 
        fecha_hasta=fecha_hasta,
        estado_label="Publicado", 
        intervalo_minimo_horas=INTERVALO_MINIMO_HORAS,
        timeout_inactividad=TIMEOUT_INACTIVIDAD
    )`

  const gitignoreContent = `# ============================================
# .gitignore - NO subir estos archivos a Git
# ============================================

# Credenciales y secretos
.env
.env.local
.env.production

# Contraseñas y tokens
*password*
*secret*
*credentials*

# Datos sensibles
licencia.json
codigos_renovacion.json

# Logs (pueden contener info sensible)
logs_comprar.txt
logs_detalle.txt
logs/
*.log

# Entornos virtuales
env_1/
venv/
.venv/
__pycache__/
*.pyc

# Archivos generados
debug_*.png
debug_*.html

# SSL
ssl/
*.pem
*.key

# Docker volumes
app_/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db`

  const cleanupScript = `#!/bin/bash
# ============================================
# limpiar_credenciales.sh
# Script para limpiar credenciales del repo
# ============================================

echo "🧹 Limpiando credenciales del repositorio..."
echo ""

# 1. Buscar archivos con credenciales hardcodeadas
echo "🔍 Buscando posibles credenciales en el código..."
echo ""

# Buscar patrones comunes de credenciales
grep -rn "CUIT = " --include="*.py" . | grep -v "os.environ" | grep -v ".env"
grep -rn "PASSWORD = " --include="*.py" . | grep -v "os.environ" | grep -v ".env"
grep -rn "password.*=.*['\\\"]" --include="*.py" . | grep -v "os.environ"
grep -rn "webhook" --include="*.py" . -i

echo ""
echo "⚠️  Si ves líneas arriba, hay credenciales expuestas."
echo ""

# 2. Crear .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cat > .env << 'EOF'
# Credenciales comprar.gob.ar
CUIT=tu_cuit_aqui
PASSWORD=tu_password_aqui

# Intervalo de ejecución
INTERVALO_HORAS=24
TIMEOUT_INACTIVIDAD=60

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
EMAIL_FROM=
EMAIL_TO=
EMAIL_REPORT_HOUR=20

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_IDS=

# Seguridad
ADMIN_USER=admin
ADMIN_PASS=
SECRET_KEY=cambia-esta-clave-secreta-larga
ALLOWED_IPS=
EOF
    echo "✅ Archivo .env creado. Editá las variables con tus datos reales."
else
    echo "ℹ️  Archivo .env ya existe."
fi

# 3. Agregar al .gitignore si no está
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo ".env" >> .gitignore
    echo "✅ .env agregado a .gitignore"
fi

# 4. Limpiar historial de Git (OPCIONAL - usar con cuidado)
echo ""
echo "============================================"
echo "⚠️  LIMPIAR HISTORIAL DE GIT"
echo "============================================"
echo ""
echo "Si ya subiste el repo con credenciales, NADIE puede verlas"
echo "aunque las borres ahora (quedan en el historial de Git)."
echo ""
echo "Opciones:"
echo "1. Crear un repo nuevo y subir solo el código limpio"
echo "2. Usar BFG Repo-Cleaner para limpiar el historial"
echo "3. Cambiar la contraseña en comprar.gob.ar AHORA MISMO"
echo ""
echo "🔴 RECOMENDACIÓN: Cambiá la contraseña YA en comprar.gob.ar"
echo "   y creá un repo nuevo desde cero."
echo ""
read -p "¿Querés ver cómo limpiar el historial? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "📋 Pasos para limpiar historial con BFG:"
    echo ""
    echo "1. Instalar BFG:"
    echo "   brew install bfg  (macOS)"
    echo "   O descargar de: https://rtyley.github.io/bfg-repo-cleaner/"
    echo ""
    echo "2. Limpiar archivos específicos:"
    echo "   bfg --delete-files .env"
    echo "   bfg --replace-text passwords.txt"
    echo ""
    echo "3. Limpiar el historial:"
    echo "   git reflog expire --expire=now --all"
    echo "   git gc --prune=now --aggressive"
    echo ""
    echo "4. Forzar push (¡cuidado!):"
    echo "   git push --force"
    echo ""
    echo "⚠️  Esto reescribe la historia. Si otros tienen el repo,"
    echo "   van a tener que clonarlo de nuevo."
fi

echo ""
echo "✅ Limpieza completada"`

  const envExample = `# ============================================
# .env.example - Plantilla de configuración
# Copiar a .env y completar con datos reales
# ============================================

# ============================================
# CREDENCIALES COMPRAR.GOB.AR
# ============================================
CUIT=20-12345678-9
PASSWORD=tu_password_segura_aqui

# ============================================
# CONFIGURACIÓN DE EJECUCIÓN
# ============================================
INTERVALO_HORAS=24
TIMEOUT_INACTIVIDAD=60

# ============================================
# EMAIL - Reporte diario
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_app_password_de_16_caracteres
EMAIL_FROM=tu_email@gmail.com
EMAIL_TO=email1@gmail.com,email2@gmail.com
EMAIL_REPORT_HOUR=20

# ============================================
# TELEGRAM BOT
# ============================================
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_IDS=123456789,987654321

# ============================================
# SEGURIDAD
# ============================================
ADMIN_USER=admin
ADMIN_PASS=genera_una_password_larga_y_segura
SECRET_KEY=genera_una_clave_aleatoria_larga_aqui
ALLOWED_IPS=`

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 flex items-center gap-3">
        <Lock className="w-7 h-7 text-red-400" />
        ⚠️ Problema de Credenciales
      </h2>
      
      {/* Alerta principal */}
      <div className="bg-red-900/40 border-2 border-red-600 rounded-xl p-6 mb-6">
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-8 h-8 text-red-400 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-xl font-bold text-red-300 mb-2">
              🔴 URGENTE: Tu contraseña está expuesta en GitHub
            </h3>
            <p className="text-red-200 mb-3">
              En tu archivo <code className="bg-red-950 px-2 py-0.5 rounded">comprar.py</code> tenés las credenciales hardcodeadas:
            </p>
            <div className="bg-red-950 rounded-lg p-4 font-mono text-sm mb-3">
              <p className="text-red-300">CUIT = "25418019"       <span className="text-red-500"># ← EXPUESTO</span></p>
              <p className="text-red-300">PASSWORD = "25418019"   <span className="text-red-500"># ← EXPUESTO</span></p>
            </div>
            <div className="bg-yellow-900/50 border border-yellow-600 rounded-lg p-3">
              <p className="text-yellow-200 font-semibold">🔴 ACCIONES INMEDIATAS:</p>
              <ol className="text-yellow-100 text-sm mt-2 space-y-1 list-decimal list-inside">
                <li><strong>Cambiá la contraseña en comprar.gob.ar AHORA MISMO</strong></li>
                <li>Eliminá el repo de GitHub o limpiá el historial</li>
                <li>Creá un repo nuevo solo con código limpio</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      {/* Explicación del problema */}
      <div className="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-3">¿Por qué es un problema?</h3>
        <div className="space-y-3 text-sm text-gray-300">
          <p>
            <strong className="text-white">1. El historial de Git es permanente:</strong> Aunque borres las credenciales ahora, 
            quedan en todos los commits anteriores. Cualquiera puede verlas con <code className="bg-gray-700 px-1 rounded">git log -p</code>.
          </p>
          <p>
            <strong className="text-white">2. Bots escanean GitHub constantemente:</strong> Hay bots automáticos que buscan 
            credenciales expuestas en repos públicos. Pueden haber sido capturadas en minutos.
          </p>
          <p>
            <strong className="text-white">3. Webhook de Discord expuesto:</strong> En <code className="bg-gray-700 px-1 rounded">run_comprar.py</code> también 
            tenés un webhook de Discord visible.
          </p>
        </div>
      </div>

      {/* Solución paso a paso */}
      <div className="bg-green-900/30 border border-green-700 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4 text-green-300 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          Solución: Mover credenciales a variables de entorno
        </h3>
        
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">1</div>
            <div className="flex-1">
              <p className="font-semibold text-sm mb-1">Cambiar la contraseña en comprar.gob.ar</p>
              <p className="text-xs text-gray-400">Entrá al sitio y cambiá la contraseña inmediatamente</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">2</div>
            <div className="flex-1">
              <p className="font-semibold text-sm mb-1">Reemplazar comprar.py con la versión segura</p>
              <p className="text-xs text-gray-400">Las credenciales ahora se leen de variables de entorno</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">3</div>
            <div className="flex-1">
              <p className="font-semibold text-sm mb-1">Crear archivo .env con tus credenciales</p>
              <p className="text-xs text-gray-400">Este archivo NUNCA se sube a Git</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">4</div>
            <div className="flex-1">
              <p className="font-semibold text-sm mb-1">Agregar .env al .gitignore</p>
              <p className="text-xs text-gray-400">Para que Git nunca lo trackee</p>
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-sm font-bold">5</div>
            <div className="flex-1">
              <p className="font-semibold text-sm mb-1">Eliminar el repo público y crear uno nuevo</p>
              <p className="text-xs text-gray-400">O hacerlo privado y limpiar el historial</p>
            </div>
          </div>
        </div>
      </div>

      {/* Archivos */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold mb-2">📄 Archivos para copiar</h3>
        
        <FileBlock
          name="comprar.py (VERSIÓN SEGURA)"
          content={comprarPatched}
          lang="python"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
        
        <FileBlock
          name=".env.example"
          content={envExample}
          lang="env"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
        
        <FileBlock
          name=".gitignore"
          content={gitignoreContent}
          lang="gitignore"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
        
        <FileBlock
          name="limpiar_credenciales.sh"
          content={cleanupScript}
          lang="bash"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
      </div>

      {/* Resumen */}
      <div className="mt-6 bg-blue-900/30 border border-blue-700 rounded-lg p-4">
        <h4 className="font-semibold text-blue-300 mb-2">💡 Resumen</h4>
        <ul className="text-sm text-blue-200/80 space-y-1 list-disc list-inside">
          <li>El código que generé está en las pestañas de este panel (podés copiar cada archivo)</li>
          <li>Tu contraseña está expuesta en GitHub - <strong>cambiala YA</strong></li>
          <li>Usá variables de entorno (.env) para todas las credenciales</li>
          <li>Nunca subas .env a Git (está en .gitignore)</li>
          <li>Si el repo es público, eliminá el historial o creá uno nuevo</li>
        </ul>
      </div>
    </div>
  )
}

// ==================== DOCKER SECTION ====================
function DockerSection({ copiedFile, copyToClipboard }: { copiedFile: string | null; copyToClipboard: (t: string, id: string) => void }) {
  const dockerfile = `FROM python:3.11-slim

# Instalar dependencias del sistema para Playwright
RUN apt-get update && apt-get install -y \\
    wget \\
    gnupg \\
    libnss3 \\
    libatk1.0-0 \\
    libatk-bridge2.0-0 \\
    libcups2 \\
    libdrm2 \\
    libxkbcommon0 \\
    libxcomposite1 \\
    libxdamage1 \\
    libxrandr2 \\
    libgbm1 \\
    libpango-1.0-0 \\
    libcairo2 \\
    libasound2 \\
    libxshmfence1 \\
    cron \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements primero (cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright con Chromium
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar el resto del código
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/detalle_procesos /app/logs /app/data

# Exponer puerto del dashboard
EXPOSE 8765

# Script de entrada que inicia todo
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]`

  const dockerCompose = `version: '3.8'

services:
  # ============================================
  # SERVIDOR PRINCIPAL - Dashboard + Scraping
  # ============================================
  app:
    build: .
    container_name: comprar_app
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - CUIT=\${CUIT}
      - PASSWORD=\${PASSWORD}
      - INTERVALO_HORAS=\${INTERVALO_HORAS:-24}
      - TIMEOUT_INACTIVIDAD=\${TIMEOUT_INACTIVIDAD:-60}
      - NOMBRE_EXCEL=procesos_armada.xlsx
      # Email
      - SMTP_HOST=\${SMTP_HOST}
      - SMTP_PORT=\${SMTP_PORT:-587}
      - SMTP_USER=\${SMTP_USER}
      - SMTP_PASS=\${SMTP_PASS}
      - EMAIL_FROM=\${EMAIL_FROM}
      - EMAIL_TO=\${EMAIL_TO}
      - EMAIL_REPORT_HOUR=\${EMAIL_REPORT_HOUR:-20}
      # Telegram
      - TELEGRAM_BOT_TOKEN=\${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_IDS=\${TELEGRAM_CHAT_IDS}
      # Seguridad
      - ADMIN_USER=\${ADMIN_USER:-admin}
      - ADMIN_PASS=\${ADMIN_PASS}
      - ALLOWED_IPS=\${ALLOWED_IPS:-}
    volumes:
      - app_data:/app/data
      - app_logs:/app/logs
      - ./detalle_procesos:/app/detalle_procesos
      - ./procesos_armada.xlsx:/app/procesos_armada.xlsx
      - ./registro_gestion.xlsx:/app/registro_gestion.xlsx
      - ./cronograma_procesos.xlsx:/app/cronograma_procesos.xlsx
      - ./estado_procesos.json:/app/estado_procesos.json
      - ./estado_detalle.json:/app/estado_detalle.json
      - ./codigos_renovacion.json:/app/codigos_renovacion.json
      - ./licencia.json:/app/licencia.json
      - ./notas_mejoras.json:/app/notas_mejoras.json
    networks:
      - comprar_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ============================================
  # NGINX - Reverse Proxy + SSL
  # ============================================
  nginx:
    image: nginx:alpine
    container_name: comprar_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - comprar_net

volumes:
  app_data:
  app_logs:

networks:
  comprar_net:
    driver: bridge`

  const requirements = `playwright==1.40.0
pandas==2.1.4
openpyxl==3.1.2
requests==2.31.0
python-telegram-bot==20.7
APScheduler==3.10.4
cryptography==41.0.7
gunicorn==21.2.0
python-dotenv==1.0.0`

  const entrypoint = `#!/bin/bash
set -e

echo "============================================"
echo "🚀 Iniciando Dashboard de Licitaciones"
echo "============================================"

# Configurar cron para reporte diario
if [ -n "$EMAIL_REPORT_HOUR" ]; then
    echo "0 $EMAIL_REPORT_HOUR * * * cd /app && python enviar_reporte_email.py >> /app/logs/cron_email.log 2>&1" > /etc/cron.d/email_report
    chmod 0644 /etc/cron.d/email_report
    crontab /etc/cron.d/email_report
    cron
    echo "✅ Cron configurado: reporte email a las \${EMAIL_REPORT_HOUR}:00"
fi

# Iniciar bot de Telegram en background
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✅ Iniciando bot de Telegram..."
    python telegram_bot.py &
fi

# Iniciar servidor principal
echo "📍 Dashboard disponible en http://0.0.0.0:8765"
exec python servidor_dashboard.py`

  const nginxConf = `events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    server {
        listen 80;
        server_name _;

        # Redirigir HTTP a HTTPS (si tenés SSL)
        # return 301 https://$host$request_uri;

        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app:8765;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout para scraping largo
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Rate limit más estricto para login
        location /api/licencia {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://app:8765;
        }

        # Bloquear acceso a archivos sensibles
        location ~ /\\.(env|git) {
            deny all;
        }
    }

    # Descomentar para HTTPS con certificado propio
    # server {
    #     listen 443 ssl;
    #     server_name tu_dominio.com;
    #     
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers HIGH:!aNULL:!MD5;
    #     
    #     location / {
    #         proxy_pass http://app:8765;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #     }
    # }
}`

  const envExample = `# ============================================
# CONFIGURACIÓN - Dashboard de Licitaciones
# ============================================

# Credenciales comprar.gob.ar
CUIT=25418019
PASSWORD=tu_password_aqui

# Intervalo de ejecución (horas)
INTERVALO_HORAS=24
TIMEOUT_INACTIVIDAD=60

# ============================================
# EMAIL - Reporte diario
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_app_password
EMAIL_FROM=tu_email@gmail.com
# Separar múltiples emails con coma
EMAIL_TO=email1@gmail.com,email2@gmail.com
EMAIL_REPORT_HOUR=20

# ============================================
# TELEGRAM BOT
# ============================================
# Obtener token de @BotFather en Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
# Obtener chat ID enviando /start al bot y luego visitando:
# https://api.telegram.org/bot<TOKEN>/getUpdates
TELEGRAM_CHAT_IDS=123456789,987654321

# ============================================
# SEGURIDAD
# ============================================
ADMIN_USER=admin
ADMIN_PASS=cambia_esta_password_segura
# IPs permitidas (vacío = todas). Separar con coma
ALLOWED_IPS=`

  const files = [
    { name: 'Dockerfile', content: dockerfile, lang: 'dockerfile' },
    { name: 'docker-compose.yml', content: dockerCompose, lang: 'yaml' },
    { name: 'requirements.txt', content: requirements, lang: 'text' },
    { name: 'entrypoint.sh', content: entrypoint, lang: 'bash' },
    { name: 'nginx.conf', content: nginxConf, lang: 'nginx' },
    { name: '.env', content: envExample, lang: 'env' },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Dockerización</h2>
      <p className="text-gray-400 mb-6">
        Todos los archivos necesarios para correr el proyecto en contenedores Docker.
      </p>

      <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
          <div>
            <p className="font-semibold text-yellow-300">Importante</p>
            <p className="text-sm text-yellow-200/80">
              Antes de dockerizar, asegurate de tener Docker y Docker Compose instalados en tu servidor.
              El servidor necesita al menos 2GB de RAM para Playwright con Chromium.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {files.map(file => (
          <FileBlock 
            key={file.name}
            name={file.name}
            content={file.content}
            lang={file.lang}
            copiedFile={copiedFile}
            copyToClipboard={copyToClipboard}
          />
        ))}
      </div>
    </div>
  )
}

// ==================== SECURITY SECTION ====================
function SecuritySection({ copiedFile, copyToClipboard }: { copiedFile: string | null; copyToClipboard: (t: string, id: string) => void }) {
  const authMiddleware = `"""
middleware_seguridad.py
Middleware de seguridad para el servidor dashboard.
Agregar al inicio de servidor_dashboard.py
"""
import hashlib
import hmac
import time
import json
import os
from functools import wraps
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
SESSION_DURATION = 3600 * 8  # 8 horas
SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esta-clave-secreta-larga")
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutos

# Almacenamiento en memoria (para producción usar Redis)
login_attempts = {}
sessions = {}
blocked_ips = {}


def verificar_ip_permitida(ip):
    """Verifica si la IP está en la lista de IPs permitidas."""
    allowed = os.environ.get("ALLOWED_IPS", "")
    if not allowed:
        return True  # Si no hay lista, permitir todas
    allowed_list = [ip.strip() for ip in allowed.split(",")]
    return ip in allowed_list


def verificar_rate_limit(ip):
    """Rate limiting por IP para prevenir fuerza bruta."""
    ahora = time.time()
    
    # Limpiar bloqueos expirados
    if ip in blocked_ips:
        if ahora - blocked_ips[ip] > LOCKOUT_DURATION:
            del blocked_ips[ip]
        else:
            return False, "IP bloqueada temporalmente. Intentá más tarde."
    
    # Verificar intentos
    if ip not in login_attempts:
        login_attempts[ip] = []
    
    # Limpiar intentos viejos (últimos 15 min)
    login_attempts[ip] = [t for t in login_attempts[ip] if ahora - t < LOCKOUT_DURATION]
    
    if len(login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
        blocked_ips[ip] = ahora
        return False, f"Demasiados intentos. IP bloqueada por {LOCKOUT_DURATION//60} min."
    
    return True, None


def registrar_intento_login(ip, exitoso=False):
    """Registra un intento de login."""
    ahora = time.time()
    if ip not in login_attempts:
        login_attempts[ip] = []
    login_attempts[ip].append(ahora)


def crear_token(username):
    """Crea un token de sesión."""
    timestamp = str(time.time())
    data = f"{username}:{timestamp}:{SECRET_KEY}"
    token = hashlib.sha256(data.encode()).hexdigest()
    sessions[token] = {
        "username": username,
        "created": time.time(),
        "expires": time.time() + SESSION_DURATION
    }
    return token


def verificar_token(token):
    """Verifica si un token es válido."""
    if token not in sessions:
        return False
    if time.time() > sessions[token]["expires"]:
        del sessions[token]
        return False
    return True


def verificar_credenciales(username, password):
    """Verifica credenciales del admin."""
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASS", "")
    
    if not admin_pass:
        return False, "No hay password de admin configurada"
    
    if username == admin_user and password == admin_pass:
        return True, None
    return False, "Credenciales inválidas"


# ============================================
# LOG DE SEGURIDAD
# ============================================
def log_seguridad(evento, ip=None, detalle=None):
    """Registra eventos de seguridad."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"[SEGURIDAD] {timestamp} | {evento}"
    if ip:
        msg += f" | IP: {ip}"
    if detalle:
        msg += f" | {detalle}"
    print(msg)
    
    # También escribir a archivo
    try:
        with open("/app/logs/seguridad.log", "a") as f:
            f.write(msg + "\\n")
    except:
        pass`

  const firewallScript = `#!/bin/bash
# ============================================
# firewall.sh - Configuración de firewall
# Ejecutar como root en el servidor host
# ============================================

echo "🔒 Configurando firewall..."

# Instalar UFW si no está
apt-get install -y ufw

# Resetear reglas
ufw --force reset

# Configurar defaults
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH (¡IMPORTANTE! Hacer antes de bloquear todo)
ufw allow 22/tcp comment 'SSH'

# Permitir HTTP/HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Permitir el puerto del dashboard SOLO desde red local (opcional)
# ufw allow from 192.168.1.0/24 to any port 8765 comment 'Dashboard LAN'

# NO exponer el puerto 8765 directamente (va por nginx)
# ufw deny 8765/tcp

# Activar firewall
ufw --force enable

echo "✅ Firewall configurado"
echo "📋 Estado:"
ufw status verbose`

  const sslScript = `#!/bin/bash
# ============================================
# generar_ssl.sh - Generar certificado SSL
# ============================================

# Opción 1: Certificado autofirmado (para testing)
echo "🔐 Generando certificado SSL autofirmado..."
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
    -keyout ssl/key.pem \\
    -out ssl/cert.pem \\
    -subj "/C=AR/ST=BA/L=BuenosAires/O=Licitaciones/CN=localhost"

echo "✅ Certificados generados en ./ssl/"
echo ""
echo "Para producción, usar Let's Encrypt:"
echo "  certbot --nginx -d tu_dominio.com"

# Opción 2: Let's Encrypt (producción)
# ============================================
# Descomentar las siguientes líneas si tenés un dominio:
# 
# apt-get install certbot python3-certbot-nginx
# certbot --nginx -d tu-dominio.com
# 
# Renovación automática:
# certbot renew --dry-run`

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Seguridad</h2>
      <p className="text-gray-400 mb-6">
        Capas de seguridad para proteger el servidor: autenticación, rate limiting, firewall y SSL.
      </p>

      {/* Security Checklist */}
      <div className="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-green-400" />
          Checklist de Seguridad
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { text: 'Autenticación con token de sesión', done: true },
            { text: 'Rate limiting (previene fuerza bruta)', done: true },
            { text: 'Bloqueo de IP tras intentos fallidos', done: true },
            { text: 'Reverse proxy con Nginx', done: true },
            { text: 'Headers de seguridad HTTP', done: true },
            { text: 'SSL/TLS (HTTPS)', done: false },
            { text: 'Firewall UFW en el host', done: false },
            { text: 'Variables de entorno (no hardcodear)', done: true },
            { text: 'Logs de seguridad', done: true },
            { text: 'Whitelist de IPs (opcional)', done: true },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              {item.done ? (
                <CheckCircle className="w-4 h-4 text-green-400" />
              ) : (
                <Clock className="w-4 h-4 text-yellow-400" />
              )}
              <span className={item.done ? 'text-gray-300' : 'text-gray-400'}>{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <FileBlock
          name="middleware_seguridad.py"
          content={authMiddleware}
          lang="python"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
        <FileBlock
          name="firewall.sh"
          content={firewallScript}
          lang="bash"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
        <FileBlock
          name="generar_ssl.sh"
          content={sslScript}
          lang="bash"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
      </div>
    </div>
  )
}

// ==================== EMAIL SECTION ====================
function EmailSection({ copiedFile, copyToClipboard }: { copiedFile: string | null; copyToClipboard: (t: string, id: string) => void }) {
  const emailScript = `"""
enviar_reporte_email.py
Envía un reporte diario por email con el estado de los procesos.
Se ejecuta automáticamente vía cron a la hora configurada.
"""
import os
import json
import smtplib
import pandas as pd
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ============================================
# CONFIGURACIÓN
# ============================================
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")  # Separado por comas

EXCEL_PROCESOS = "procesos_armada.xlsx"
EXCEL_GESTION = "registro_gestion.xlsx"
ESTADO_PROCESOS = "estado_procesos.json"
LOG_FILE = "logs_comprar.txt"


def cargar_destinatarios():
    """Carga la lista de destinatarios desde la variable de entorno."""
    if not EMAIL_TO:
        return []
    return [email.strip() for email in EMAIL_TO.split(",") if email.strip()]


def generar_reporte_html():
    """Genera el contenido HTML del reporte."""
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Cargar estado de procesos
    procesos_activos = 0
    procesos_nuevos = 0
    try:
        with open(ESTADO_PROCESOS, "r") as f:
            estado = json.load(f)
        procesos_activos = len(estado.get("procesos", {}))
        ultima = estado.get("ultima_ejecucion", "Nunca")
    except:
        ultima = "Error al cargar"
    
    # Cargar datos del Excel si existe
    tabla_html = ""
    if os.path.exists(EXCEL_PROCESOS):
        try:
            df = pd.read_excel(EXCEL_PROCESOS)
            procesos_nuevos = len(df)
            
            # Generar tabla HTML (primeras 20 filas)
            df_preview = df.head(20)
            tabla_html = "<table style='border-collapse:collapse;width:100%;font-size:12px'>"
            tabla_html += "<tr style='background:#1a365d;color:white'>"
            for col in df_preview.columns[:6]:  # Solo primeras 6 columnas
                tabla_html += f"<th style='padding:8px;border:1px solid #ddd;text-align:left'>{col}</th>"
            tabla_html += "</tr>"
            
            for _, row in df_preview.iterrows():
                tabla_html += "<tr style='background:#f8f9fa'>"
                for col in df_preview.columns[:6]:
                    valor = str(row.get(col, ""))[:40]
                    tabla_html += f"<td style='padding:6px;border:1px solid #ddd'>{valor}</td>"
                tabla_html += "</tr>"
            
            tabla_html += "</table>"
            if len(df) > 20:
                tabla_html += f"<p style='color:#666;font-size:11px'>Mostrando 20 de {len(df)} procesos</p>"
        except Exception as e:
            tabla_html = f"<p>Error leyendo Excel: {e}</p>"
    
    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px">
        <div style="background:linear-gradient(135deg,#1a365d,#2d3748);padding:20px;border-radius:10px;color:white;margin-bottom:20px">
            <h1 style="margin:0;font-size:22px">📊 Reporte Diario de Licitaciones</h1>
            <p style="margin:5px 0 0;opacity:0.8">Generado: {hoy}</p>
        </div>
        
        <div style="display:flex;gap:15px;margin-bottom:20px">
            <div style="flex:1;background:#e6fffa;padding:15px;border-radius:8px;text-align:center">
                <div style="font-size:28px;font-weight:bold;color:#234e52">{procesos_activos}</div>
                <div style="font-size:12px;color:#2c7a7b">Procesos Activos</div>
            </div>
            <div style="flex:1;background:#ebf8ff;padding:15px;border-radius:8px;text-align:center">
                <div style="font-size:28px;font-weight:bold;color:#2a4365">{procesos_nuevos}</div>
                <div style="font-size:12px;color:#2b6cb0">En Excel</div>
            </div>
            <div style="flex:1;background:#faf5ff;padding:15px;border-radius:8px;text-align:center">
                <div style="font-size:14px;font-weight:bold;color:#553c9a;margin-top:8px">{ultima[:16] if ultima != 'Nunca' else 'Nunca'}</div>
                <div style="font-size:12px;color:#6b46c1">Última Ejecución</div>
            </div>
        </div>
        
        <h2 style="color:#1a365d;font-size:16px">📋 Procesos Vigentes</h2>
        {tabla_html if tabla_html else "<p>No hay datos disponibles.</p>"}
        
        <hr style="margin:20px 0;border:none;border-top:1px solid #eee">
        <p style="font-size:11px;color:#999;text-align:center">
            Dashboard de Licitaciones - Reporte automático<br>
            Este email fue generado por el servidor Docker.
        </p>
    </body>
    </html>
    """
    return html


def enviar_email():
    """Envía el reporte por email."""
    destinatarios = cargar_destinatarios()
    
    if not destinatarios:
        print("❌ No hay destinatarios configurados (EMAIL_TO)")
        return False
    
    if not SMTP_USER or not SMTP_PASS:
        print("❌ No hay credenciales SMTP configuradas")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = ', '.join(destinatarios)
        msg['Subject'] = f"📊 Reporte Licitaciones - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Body HTML
        html = generar_reporte_html()
        msg.attach(MIMEText(html, 'html'))
        
        # Adjuntar Excel si existe
        if os.path.exists(EXCEL_PROCESOS):
            with open(EXCEL_PROCESOS, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=EXCEL_PROCESOS)
                msg.attach(part)
        
        # Enviar
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Reporte enviado a {len(destinatarios)} destinatarios")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False


if __name__ == "__main__":
    print(f"📧 Enviando reporte diario - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    enviar_email()`

  const emailConfigUI = `"""
api_emails.py
Endpoints para gestionar la lista de emails de reporte.
Agregar a servidor_dashboard.py
"""
import json
import os

EMAILS_FILE = "/app/data/emails_reporte.json"

def cargar_emails():
    """Carga la lista de emails configurados."""
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            return json.load(f)
    return {"emails": [], "updated": None}

def guardar_emails(data):
    """Guarda la lista de emails."""
    from datetime import datetime
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def agregar_email(email):
    """Agrega un email a la lista."""
    data = cargar_emails()
    if email not in data["emails"]:
        data["emails"].append(email)
        guardar_emails(data)
        return {"ok": True, "mensaje": f"Email {email} agregado"}
    return {"ok": False, "error": "Email ya existe"}

def eliminar_email(email):
    """Elimina un email de la lista."""
    data = cargar_emails()
    if email in data["emails"]:
        data["emails"].remove(email)
        guardar_emails(data)
        return {"ok": True, "mensaje": f"Email {email} eliminado"}
    return {"ok": False, "error": "Email no encontrado"}

def enviar_test(email):
    """Envía un email de prueba."""
    import smtplib
    from email.mime.text import MIMEText
    from datetime import datetime
    
    try:
        msg = MIMEText(f"✅ Email de prueba enviado correctamente.\\nFecha: {datetime.now()}")
        msg['Subject'] = '📧 Test - Dashboard Licitaciones'
        msg['From'] = os.environ.get("EMAIL_FROM")
        msg['To'] = email
        
        server = smtplib.SMTP(os.environ.get("SMTP_HOST"), int(os.environ.get("SMTP_PORT", 587)))
        server.starttls()
        server.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
        server.send_message(msg)
        server.quit()
        return {"ok": True, "mensaje": "Email de prueba enviado"}
    except Exception as e:
        return {"ok": False, "error": str(e)}`

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Reportes por Email</h2>
      <p className="text-gray-400 mb-6">
        Sistema de reportes diarios automáticos. Se envía un email con el estado de los procesos 
        a las direcciones que configures.
      </p>

      {/* Gmail Setup Guide */}
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-300 mb-2">📧 Configuración de Gmail (App Password)</h3>
        <ol className="text-sm text-blue-200/80 space-y-1 list-decimal list-inside">
          <li>Ir a <a href="https://myaccount.google.com/apppasswords" target="_blank" className="underline">myaccount.google.com/apppasswords</a></li>
          <li>Activar verificación en 2 pasos si no está activa</li>
          <li>Generar una "App Password" (Contraseña de aplicación)</li>
          <li>Copiar la contraseña de 16 caracteres y ponerla en <code className="bg-gray-800 px-1 rounded">SMTP_PASS</code></li>
        </ol>
      </div>

      {/* Email Flow */}
      <div className="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">🔄 Flujo del Reporte</h3>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <div className="bg-gray-700 px-3 py-2 rounded-lg">⏰ Cron (hora configurable)</div>
          <ChevronRight className="w-4 h-4 text-gray-500" />
          <div className="bg-gray-700 px-3 py-2 rounded-lg">📊 Genera reporte HTML</div>
          <ChevronRight className="w-4 h-4 text-gray-500" />
          <div className="bg-gray-700 px-3 py-2 rounded-lg">📎 Adjunta Excel</div>
          <ChevronRight className="w-4 h-4 text-gray-500" />
          <div className="bg-gray-700 px-3 py-2 rounded-lg">📧 Envía SMTP</div>
          <ChevronRight className="w-4 h-4 text-gray-500" />
          <div className="bg-green-900/50 px-3 py-2 rounded-lg border border-green-700">✅ Destinatarios</div>
        </div>
      </div>

      <div className="space-y-4">
        <FileBlock
          name="enviar_reporte_email.py"
          content={emailScript}
          lang="python"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
        <FileBlock
          name="api_emails.py"
          content={emailConfigUI}
          lang="python"
          copiedFile={copiedFile}
          copyToClipboard={copyToClipboard}
        />
      </div>
    </div>
  )
}

// ==================== TELEGRAM SECTION ====================
function TelegramSection({ copiedFile, copyToClipboard }: { copiedFile: string | null; copyToClipboard: (t: string, id: string) => void }) {
  const telegramBot = `"""
telegram_bot.py
Bot de Telegram interactivo para monitoreo y control remoto.

Comandos disponibles:
  /estado    - Estado actual de los procesos
  /procesos  - Lista de procesos vigentes
  /ejecutar  - Forzar ejecución del scraping
  /reporte   - Enviar reporte ahora
  /logs      - Últimas líneas del log
  /help      - Ayuda
  /agregar_email - Agregar email a reportes
  /quitar_email  - Quitar email de reportes
  /emails    - Ver lista de emails configurados
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ============================================
# CONFIGURACIÓN
# ============================================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_IDS = os.environ.get("TELEGRAM_CHAT_IDS", "")  # Separados por coma
ESTADO_FILE = "estado_procesos.json"
EXCEL_FILE = "procesos_armada.xlsx"
LOG_FILE = "logs_comprar.txt"
EMAILS_FILE = "/app/data/emails_reporte.json"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_allowed_chats():
    """Retorna la lista de chat IDs autorizados."""
    if not CHAT_IDS:
        return []
    return [int(cid.strip()) for cid in CHAT_IDS.split(",") if cid.strip()]


def is_authorized(update: Update) -> bool:
    """Verifica si el chat está autorizado."""
    chat_id = update.effective_chat.id
    allowed = get_allowed_chats()
    if not allowed:
        return True  # Si no hay lista, permitir todos
    return chat_id in allowed


# ============================================
# COMANDOS
# ============================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🤖 *Dashboard de Licitaciones*\\n\\n"
        f"Tu Chat ID: \`{chat_id}\`\\n\\n"
        f"Comandos disponibles:\\n"
        f"/estado - Estado de procesos\\n"
        f"/procesos - Lista vigentes\\n"
        f"/ejecutar - Forzar scraping\\n"
        f"/reporte - Enviar reporte email\\n"
        f"/logs - Últimos logs\\n"
        f"/emails - Ver emails reporte\\n"
        f"/agregar\\_email - Agregar email\\n"
        f"/quitar\\_email - Quitar email\\n"
        f"/help - Esta ayuda",
        parse_mode='Markdown'
    )


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Estado actual del sistema."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        with open(ESTADO_FILE, "r") as f:
            estado = json.load(f)
        
        ultima = estado.get("ultima_ejecucion", "Nunca")
        num_procesos = len(estado.get("procesos", {}))
        
        # Calcular tiempo desde última ejecución
        tiempo_str = ""
        if ultima != "Nunca":
            try:
                ultima_dt = datetime.fromisoformat(ultima)
                diff = datetime.now() - ultima_dt
                horas = diff.total_seconds() / 3600
                if horas < 1:
                    tiempo_str = f"hace {int(diff.total_seconds()/60)} min"
                else:
                    tiempo_str = f"hace {horas:.1f} horas"
            except:
                tiempo_str = ultima
        
        msg = (
            f"📊 *Estado del Sistema*\\n\\n"
            f"🔄 Procesos activos: *{num_procesos}*\\n"
            f"⏰ Última ejecución: {tiempo_str}\\n"
            f"📅 Fecha última: {ultima[:16] if ultima != 'Nunca' else 'Nunca'}\\n\\n"
            f"🟢 Sistema operativo"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_procesos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista los procesos vigentes."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        if not os.path.exists(EXCEL_FILE):
            await update.message.reply_text("📭 No hay datos. Esperá a la primera ejecución.")
            return
        
        df = pd.read_excel(EXCEL_FILE)
        total = len(df)
        
        # Mostrar primeros 10
        msg = f"📋 *Procesos Vigentes* ({total} total)\\n\\n"
        
        for i, (_, row) in enumerate(df.head(10).iterrows()):
            numero = row.get('Número de proceso', 'N/A')
            organismo = row.get('Organismo', 'N/A')[:30]
            estado = row.get('Estado de proceso', 'N/A')
            msg += f"*{i+1}.* \`{numero}\`\\n   {organismo}\\n   Estado: {estado}\\n\\n"
        
        if total > 10:
            msg += f"_... y {total - 10} más. Ver dashboard para completo._"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_ejecutar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fuerza la ejecución del scraping."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    await update.message.reply_text("🔄 Iniciando ejecución forzada... Esto puede tardar varios minutos.")
    
    try:
        import subprocess
        env = os.environ.copy()
        env["FORZAR_EJECUCION"] = "1"
        
        result = subprocess.run(
            ["python", "comprar.py"],
            capture_output=True, text=True, timeout=600,
            env=env, cwd="/app"
        )
        
        if result.returncode == 0:
            await update.message.reply_text("✅ Ejecución completada exitosamente.")
        else:
            await update.message.reply_text(f"⚠️ Ejecución terminó con warnings.\\n\`{result.stderr[-500:]}\`", parse_mode='Markdown')
            
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏰ Timeout: la ejecución tardó más de 10 minutos.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el reporte por email inmediatamente."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    await update.message.reply_text("📧 Enviando reporte por email...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "enviar_reporte_email.py"],
            capture_output=True, text=True, timeout=60,
            cwd="/app"
        )
        
        if result.returncode == 0:
            await update.message.reply_text("✅ Reporte enviado correctamente.")
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr[-300:]}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las últimas líneas del log."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        ultimas = lines[-15:] if len(lines) > 15 else lines
        msg = "📝 *Últimos logs:*\\n\\n\`" + "".join(ultimas[-10:]) + "\`"
        
        # Telegram tiene límite de 4096 chars
        if len(msg) > 4000:
            msg = msg[:4000] + "\\n... (truncado)"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error leyendo logs: {e}")


async def cmd_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de emails configurados."""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    try:
        if os.path.exists(EMAILS_FILE):
            with open(EMAILS_FILE, "r") as f:
                data = json.load(f)
            emails = data.get("emails", [])
        else:
            emails = os.environ.get("EMAIL_TO", "").split(",")
        
        if emails:
            msg = "📧 *Emails para reportes:*\\n\\n"
            for i, email in enumerate(emails, 1):
                msg += f"{i}. \`{email.strip()}\`\\n"
            msg += "\\nUsá /agregar\\_email o /quitar\\_email para modificar"
        else:
            msg = "📭 No hay emails configurados.\\nUsá /agregar\\_email para agregar."
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_agregar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Agrega un email. Uso: /agregar_email usuario@dominio.com"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: /agregar\\_email usuario@dominio.com", parse_mode='Markdown')
        return
    
    email = context.args[0].strip()
    
    # Guardar en archivo
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"emails": []}
    
    if email in data["emails"]:
        await update.message.reply_text(f"⚠️ {email} ya está en la lista.")
        return
    
    data["emails"].append(email)
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f)
    
    await update.message.reply_text(f"✅ {email} agregado a reportes.")


async def cmd_quitar_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quita un email. Uso: /quitar_email usuario@dominio.com"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ No autorizado.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: /quitar\\_email usuario@dominio.com", parse_mode='Markdown')
        return
    
    email = context.args[0].strip()
    
    if os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"emails": []}
    
    if email not in data["emails"]:
        await update.message.reply_text(f"⚠️ {email} no está en la lista.")
        return
    
    data["emails"].remove(email)
    data["updated"] = datetime.now().isoformat()
    with open(EMAILS_FILE, "w") as f:
        json.dump(data, f)
    
    await update.message.reply_text(f"✅ {email} eliminado de reportes.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ayuda."""
    await cmd_start(update, context)


# ============================================
# MAIN
# ============================================
def main():
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN no configurado")
        return
    
    logger.info("🤖 Iniciando bot de Telegram...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Registrar comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("estado", cmd_estado))
    app.add_handler(CommandHandler("procesos", cmd_procesos))
    app.add_handler(CommandHandler("ejecutar", cmd_ejecutar))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(CommandHandler("emails", cmd_emails))
    app.add_handler(CommandHandler("agregar_email", cmd_agregar_email))
    app.add_handler(CommandHandler("quitar_email", cmd_quitar_email))
    app.add_handler(CommandHandler("help", cmd_help))
    
    # Configurar comandos en el menú del bot
    import asyncio
    async def setup_commands():
        commands = [
            BotCommand("estado", "Estado del sistema"),
            BotCommand("procesos", "Lista de procesos"),
            BotCommand("ejecutar", "Forzar ejecución"),
            BotCommand("reporte", "Enviar reporte email"),
            BotCommand("logs", "Ver últimos logs"),
            BotCommand("emails", "Emails configurados"),
            BotCommand("agregar_email", "Agregar email"),
            BotCommand("quitar_email", "Quitar email"),
            BotCommand("help", "Ayuda"),
        ]
        await app.bot.set_my_commands(commands)
    
    asyncio.get_event_loop().run_until_complete(setup_commands())
    
    logger.info("✅ Bot iniciado. Esperando mensajes...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()`

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Bot de Telegram</h2>
      <p className="text-gray-400 mb-6">
        Bot interactivo para monitorear y controlar el sistema desde Telegram. 
        Podés ver el estado, forzar ejecuciones, gestionar emails y ver logs.
      </p>

      {/* Setup Guide */}
      <div className="bg-purple-900/30 border border-purple-700 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-purple-300 mb-2">🤖 Crear el Bot en Telegram</h3>
        <ol className="text-sm text-purple-200/80 space-y-2 list-decimal list-inside">
          <li>Abrir Telegram y buscar <code className="bg-gray-800 px-1 rounded">@BotFather</code></li>
          <li>Enviar <code className="bg-gray-800 px-1 rounded">/newbot</code></li>
          <li>Elegir un nombre y username para el bot</li>
          <li>Copiar el <strong>token</strong> que te da (formato: 123456:ABCdef...)</li>
          <li>Ponerlo en <code className="bg-gray-800 px-1 rounded">TELEGRAM_BOT_TOKEN</code> del .env</li>
          <li>Abrir tu bot y enviar <code className="bg-gray-800 px-1 rounded">/start</code></li>
          <li>Visitar <code className="bg-gray-800 px-1 rounded text-xs">https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</code></li>
          <li>Copiar tu <code className="bg-gray-800 px-1 rounded">chat.id</code> y ponerlo en <code className="bg-gray-800 px-1 rounded">TELEGRAM_CHAT_IDS</code></li>
        </ol>
      </div>

      {/* Commands Grid */}
      <div className="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">📱 Comandos del Bot</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { cmd: '/estado', desc: 'Ver estado del sistema y procesos activos' },
            { cmd: '/procesos', desc: 'Lista los primeros 10 procesos vigentes' },
            { cmd: '/ejecutar', desc: 'Forzar ejecución del scraping ahora' },
            { cmd: '/reporte', desc: 'Enviar reporte por email inmediatamente' },
            { cmd: '/logs', desc: 'Ver las últimas líneas del log' },
            { cmd: '/emails', desc: 'Ver lista de emails para reportes' },
            { cmd: '/agregar_email', desc: 'Agregar un email a los reportes' },
            { cmd: '/quitar_email', desc: 'Quitar un email de los reportes' },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-3 bg-gray-700/50 rounded-lg p-3">
              <code className="text-green-400 text-sm font-mono whitespace-nowrap">{item.cmd}</code>
              <span className="text-gray-400 text-sm">{item.desc}</span>
            </div>
          ))}
        </div>
      </div>

      <FileBlock
        name="telegram_bot.py"
        content={telegramBot}
        lang="python"
        copiedFile={copiedFile}
        copyToClipboard={copyToClipboard}
      />
    </div>
  )
}

// ==================== FILES SECTION ====================
function FilesSection({ expandedFile, setExpandedFile, copiedFile, copyToClipboard }: { 
  expandedFile: string | null; setExpandedFile: (f: string | null) => void; copiedFile: string | null; copyToClipboard: (t: string, id: string) => void
}) {
  
  const downloadableFiles = [
    { name: 'comprar.py', desc: 'Versión segura (sin credenciales hardcodeadas)', category: 'Python' },
    { name: 'servidor_dashboard.py', desc: 'Servidor con integraciones de seguridad, email y telegram', category: 'Python' },
    { name: 'enviar_reporte_email.py', desc: 'Reporte diario por email con HTML y Excel adjunto', category: 'Python' },
    { name: 'telegram_bot.py', desc: 'Bot de Telegram con comandos interactivos', category: 'Python' },
    { name: 'middleware_seguridad.py', desc: 'Autenticación, rate limiting, bloqueo de IPs', category: 'Python' },
    { name: 'api_emails.py', desc: 'Gestión de emails para reportes', category: 'Python' },
    { name: 'requirements.txt', desc: 'Dependencias Python actualizadas', category: 'Config' },
    { name: '.env.example', desc: 'Plantilla de variables de entorno', category: 'Config' },
    { name: '.gitignore', desc: 'Ignorar archivos sensibles en Git', category: 'Config' },
    { name: 'Dockerfile', desc: 'Imagen del contenedor con Playwright', category: 'Docker' },
    { name: 'docker-compose.yml', desc: 'Orquestación de servicios (app + nginx)', category: 'Docker' },
    { name: 'nginx.conf', desc: 'Reverse proxy con seguridad y rate limiting', category: 'Docker' },
    { name: 'entrypoint.sh', desc: 'Script de inicio del contenedor', category: 'Docker' },
    { name: 'firewall.sh', desc: 'Configuración de firewall UFW', category: 'Seguridad' },
    { name: 'generar_ssl.sh', desc: 'Generar certificados SSL', category: 'Seguridad' },
    { name: 'limpiar_credenciales.sh', desc: 'Limpiar credenciales del repo', category: 'Seguridad' },
    { name: 'README.md', desc: 'Documentación completa del proyecto', category: 'Docs' },
  ]
  
  const categories = ['Python', 'Config', 'Docker', 'Seguridad', 'Docs']

  const allFiles = [
    {
      name: 'Estructura del Proyecto',
      content: `comprar/├── 📄 docker-compose.yml          # Orquestación de contenedores
├── 📄 Dockerfile                  # Imagen del contenedor principal
├── 📄 .env                        # Variables de entorno (NO subir a git)
├── 📄 nginx.conf                  # Configuración del reverse proxy
├── 📄 requirements.txt            # Dependencias Python
├── 📄 entrypoint.sh               # Script de inicio del contenedor
├── 📄 middleware_seguridad.py     # Autenticación y rate limiting
├── 📄 enviar_reporte_email.py    # Reporte diario por email
├── 📄 api_emails.py              # API para gestionar emails
├── 📄 telegram_bot.py            # Bot de Telegram
├── 📄 firewall.sh                # Script de firewall
├── 📄 generar_ssl.sh             # Generar certificados SSL
│
├── 📁 ssl/                       # Certificados SSL
│   ├── cert.pem
│   └── key.pem
│
├── 📁 data/                      # Datos persistentes
│   └── emails_reporte.json
│
├── 📁 logs/                      # Logs del sistema
│   ├── comprar.log
│   ├── seguridad.log
│   └── cron_email.log
│
│─── Archivos originales del repo ───
├── 📄 comprar.py                 # Script principal de scraping
├── 📄 servidor_dashboard.py      # Servidor del dashboard
├── 📄 generar_dashboard.py       # Generador del HTML
├── 📄 detalle_proceso.py         # Detalle de procesos
├── 📄 licencia.py                # Sistema de licencias
├── 📄 dashboard.html             # Dashboard web
├── 📄 procesos_armada.xlsx       # Excel de procesos
├── 📄 registro_gestion.xlsx      # Registro de gestión
├── 📄 cronograma_procesos.xlsx   # Cronograma
├── 📄 estado_procesos.json       # Estado actual
├── 📄 estado_detalle.json        # Estado detalle
├── 📄 codigos_renovacion.json    # Códigos de licencia
├── 📄 licencia.json              # Licencia actual
├── 📄 notas_mejoras.json         # Notas
├── 📁 detalle_procesos/          # PDFs de procesos
└── 📁 env_1/                     # Entorno virtual (no necesario con Docker)`
    }
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Archivos del Proyecto</h2>
      <p className="text-gray-400 mb-6">
        Todos los archivos están listos para descargar. Copiá los archivos a tu proyecto local.
      </p>

      {/* Download Section */}
      <div className="bg-green-900/30 border border-green-700 rounded-xl p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-green-300">
          <Download className="w-5 h-5" />
          📥 Archivos para Descargar
        </h3>
        <p className="text-sm text-green-200/80 mb-4">
          Estos archivos están en la carpeta <code className="bg-gray-800 px-1 rounded">/public/archivos/</code> del workspace.
          Podés descargarlos directamente o copiarlos desde las pestañas anteriores.
        </p>
        
        {categories.map(cat => (
          <div key={cat} className="mb-4">
            <h4 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wide">{cat}</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {downloadableFiles.filter(f => f.category === cat).map(file => (
                <a
                  key={file.name}
                  href={`/archivos/${file.name}`}
                  download
                  className="flex items-center gap-3 bg-gray-800 hover:bg-gray-700 rounded-lg p-3 border border-gray-700 hover:border-gray-500 transition-all group"
                >
                  <FileCode className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-white truncate">{file.name}</p>
                    <p className="text-xs text-gray-400 truncate">{file.desc}</p>
                  </div>
                  <Download className="w-4 h-4 text-gray-500 group-hover:text-green-400 transition-colors" />
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* File Tree */}
      <div className="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileCode className="w-5 h-5 text-blue-400" />
          Árbol de Archivos
        </h3>
        <pre className="text-sm text-gray-300 font-mono whitespace-pre overflow-x-auto bg-gray-900 p-4 rounded-lg">
          {allFiles[0].content}
        </pre>
      </div>

      {/* Deployment Steps */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-green-400" />
          Pasos de Despliegue
        </h3>
        <div className="space-y-4">
          {[
            { step: 1, title: 'Preparar el servidor', cmd: '# En tu servidor Linux/Windows con Docker\nsudo apt update && sudo apt install docker.io docker-compose -y\n# O en Windows: instalar Docker Desktop' },
            { step: 2, title: 'Clonar el repo', cmd: 'git clone https://github.com/ematevez/comprar.git\ncd comprar' },
            { step: 3, title: 'Copiar archivos nuevos', cmd: '# Copiar Dockerfile, docker-compose.yml, .env, etc.\n# desde este panel (pestañas Docker, Seguridad, Email, Telegram)' },
            { step: 4, title: 'Configurar variables', cmd: 'nano .env\n# Completar con tus credenciales reales' },
            { step: 5, title: 'Configurar firewall', cmd: 'sudo bash firewall.sh' },
            { step: 6, title: 'Levantar servicios', cmd: 'docker compose up -d\n# Ver logs:\ndocker compose logs -f' },
            { step: 7, title: 'Verificar', cmd: '# Dashboard:\ncurl http://localhost:8765\n# Telegram: enviar /start al bot\n# Email: esperar al cron o ejecutar manualmente:\ndocker compose exec app python enviar_reporte_email.py' },
          ].map(item => (
            <div key={item.step} className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold">
                {item.step}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-sm mb-1">{item.title}</p>
                <pre className="text-xs text-gray-400 bg-gray-900 p-3 rounded-lg font-mono whitespace-pre-wrap">
                  {item.cmd}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ==================== FILE BLOCK COMPONENT ====================
function FileBlock({ name, content, lang, copiedFile, copyToClipboard }: {
  name: string; content: string; lang: string; copiedFile: string | null; copyToClipboard: (t: string, id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const isCopied = copiedFile === name

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-750 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <FileCode className="w-4 h-4 text-blue-400" />
          <span className="font-mono text-sm font-semibold">{name}</span>
          <span className="text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded">{lang}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-700 transition-all"
          >
            {expanded ? 'Colapsar' : 'Expandir'}
          </button>
          <button
            onClick={() => copyToClipboard(content, name)}
            className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded transition-all ${
              isCopied 
                ? 'bg-green-600 text-white' 
                : 'bg-blue-600 hover:bg-blue-500 text-white'
            }`}
          >
            {isCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {isCopied ? 'Copiado!' : 'Copiar'}
          </button>
        </div>
      </div>
      {expanded && (
        <div className="overflow-auto max-h-96">
          <pre className="text-xs text-gray-300 p-4 font-mono whitespace-pre">
            {content}
          </pre>
        </div>
      )}
    </div>
  )
}

export default App
