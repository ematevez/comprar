#!/bin/bash
# ============================================
# instalar_docker.sh
# Script de instalación rápida para Linux/Mac
# ============================================

echo "============================================================"
echo "  🐳 Instalación Rápida de Docker para Dashboard"
echo "============================================================"
echo ""

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    echo ""
    echo "📋 Instalando Docker..."
    echo ""
    
    # Detectar sistema operativo
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y docker.io docker-compose
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            echo "✅ Docker instalado en Linux (Ubuntu/Debian)"
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y docker docker-compose
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            echo "✅ Docker instalado en Linux (Fedora)"
        else
            echo "❌ Sistema Linux no soportado automáticamente"
            echo "   Instalá Docker manualmente: https://docs.docker.com/engine/install/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac
        echo "⚠️  En macOS, instalá Docker Desktop manualmente:"
        echo "   https://www.docker.com/products/docker-desktop/"
        echo ""
        echo "   Después de instalar, volvé a ejecutar este script"
        exit 1
    else
        echo "❌ Sistema operativo no soportado"
        exit 1
    fi
    
    echo ""
    echo "⚠️  IMPORTANTE: Cerrá sesión y volvé a entrar para aplicar los permisos de Docker"
    exit 0
else
    echo "✅ Docker ya está instalado"
    docker --version
fi

echo ""
echo "============================================================"
echo "  📦 Configurando el proyecto..."
echo "============================================================"
echo ""

# Cambiar al directorio del proyecto
cd "$(dirname "$0")"

# Copiar archivos Docker si no existen
echo "📋 Copiando archivos Docker..."
[ ! -f Dockerfile ] && cp public/archivos/Dockerfile .
[ ! -f docker-compose.yml ] && cp public/archivos/docker-compose.yml .
[ ! -f entrypoint.sh ] && cp public/archivos/entrypoint.sh .
[ ! -f nginx.conf ] && cp public/archivos/nginx.conf .
[ ! -f .dockerignore ] && cp public/archivos/.dockerignore .

echo "✅ Archivos Docker copiados"

# Verificar .env
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No se encontró el archivo .env"
    echo "   Copiando .env.example a .env..."
    cp .env.example .env 2>/dev/null || echo "❌ No se encontró .env.example"
    echo ""
    echo "📝 Editá el archivo .env con tus credenciales:"
    echo "   nano .env"
    echo ""
    read -p "¿Querés editar el .env ahora? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        nano .env
    fi
fi

# Crear directorios necesarios
echo ""
echo "📁 Creando directorios necesarios..."
mkdir -p data logs detalle_procesos

# Crear archivos JSON si no existen
[ ! -f notas_mejoras.json ] && echo '{"notas": []}' > notas_mejoras.json
[ ! -f estado_procesos.json ] && echo '{"procesos": {}}' > estado_procesos.json
[ ! -f codigos_renovacion.json ] && echo '{"codigos": []}' > codigos_renovacion.json

echo "✅ Directorios y archivos creados"

echo ""
echo "============================================================"
echo "  🏗️  Construyendo la imagen Docker..."
echo "============================================================"
echo ""
echo "⏳ Esto puede tardar 5-10 minutos la primera vez..."
echo ""

# Construir la imagen
docker-compose build

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error construyendo la imagen"
    echo "   Revisá los logs arriba para ver el problema"
    exit 1
fi

echo ""
echo "✅ Imagen construida exitosamente"

echo ""
echo "============================================================"
echo "  🚀 Levantando los contenedores..."
echo "============================================================"
echo ""

# Levantar los contenedores
docker-compose up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error levantando los contenedores"
    docker-compose logs
    exit 1
fi

echo ""
echo "✅ Contenedores levantados exitosamente"

echo ""
echo "============================================================"
echo "  📊 Estado de los contenedores"
echo "============================================================"
echo ""

docker-compose ps

echo ""
echo "============================================================"
echo "  ✅ ¡INSTALACIÓN COMPLETADA!"
echo "============================================================"
echo ""
echo "📍 Accedé al dashboard en:"
echo "   http://localhost:8765"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs:        docker-compose logs -f"
echo "   Reiniciar:       docker-compose restart"
echo "   Detener:         docker-compose down"
echo "   Estado:          docker-compose ps"
echo ""
echo "📖 Para más información, leé: GUIA_DOCKER.md"
echo ""
echo "🤖 Si configuraste Telegram, el bot se inició automáticamente"
echo "📧 Si configuraste Email, los reportes se enviarán automáticamente"
echo ""
