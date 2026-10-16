#!/bin/bash
# ============================================
# backup.sh
# Script para hacer backup de los datos
# ============================================

echo "============================================================"
echo "  💾 Backup de Datos del Dashboard"
echo "============================================================"
echo ""

# Cambiar al directorio del proyecto
cd "$(dirname "$0")"

# Crear nombre de backup con fecha
FECHA=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$FECHA"

echo "📁 Creando backup en: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Verificar si Docker está corriendo
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Los contenedores no están corriendo"
    echo "   Intentando hacer backup de archivos locales..."
    
    # Copiar archivos locales si existen
    [ -f procesos_armada.xlsx ] && cp procesos_armada.xlsx "$BACKUP_DIR/"
    [ -f registro_gestion.xlsx ] && cp registro_gestion.xlsx "$BACKUP_DIR/"
    [ -f cronograma_procesos.xlsx ] && cp cronograma_procesos.xlsx "$BACKUP_DIR/"
    [ -f estado_procesos.json ] && cp estado_procesos.json "$BACKUP_DIR/"
    [ -f notas_mejoras.json ] && cp notas_mejoras.json "$BACKUP_DIR/"
    [ -f estado_detalle.json ] && cp estado_detalle.json "$BACKUP_DIR/"
    [ -d data ] && cp -r data "$BACKUP_DIR/"
    [ -d detalle_procesos ] && cp -r detalle_procesos "$BACKUP_DIR/"
    
    echo "✅ Backup de archivos locales completado"
else
    echo "🐳 Copiando datos desde el contenedor Docker..."
    
    # Copiar archivos principales
    docker cp comprar_app:/app/procesos_armada.xlsx "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  procesos_armada.xlsx no encontrado"
    docker cp comprar_app:/app/registro_gestion.xlsx "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  registro_gestion.xlsx no encontrado"
    docker cp comprar_app:/app/cronograma_procesos.xlsx "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  cronograma_procesos.xlsx no encontrado"
    docker cp comprar_app:/app/estado_procesos.json "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  estado_procesos.json no encontrado"
    docker cp comprar_app:/app/notas_mejoras.json "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  notas_mejoras.json no encontrado"
    docker cp comprar_app:/app/estado_detalle.json "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  estado_detalle.json no encontrado"
    
    # Copiar directorios
    docker cp comprar_app:/app/data "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  data/ no encontrado"
    docker cp comprar_app:/app/detalle_procesos "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  detalle_procesos/ no encontrado"
    docker cp comprar_app:/app/logs "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  logs/ no encontrado"
    
    echo "✅ Backup desde Docker completado"
fi

# Mostrar contenido del backup
echo ""
echo "📦 Contenido del backup:"
ls -lh "$BACKUP_DIR"

# Calcular tamaño total
TAMANIO=$(du -sh "$BACKUP_DIR" | cut -f1)
echo ""
echo "💾 Tamaño total: $TAMANIO"

# Comprimir backup
echo ""
read -p "¿Querés comprimir el backup en un ZIP? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if command -v zip &> /dev/null; then
        zip -r "${BACKUP_DIR}.zip" "$BACKUP_DIR"
        echo "✅ Backup comprimido: ${BACKUP_DIR}.zip"
        
        read -p "¿Querés eliminar la carpeta sin comprimir? (s/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            rm -rf "$BACKUP_DIR"
            echo "✅ Carpeta sin comprimir eliminada"
        fi
    else
        echo "⚠️  zip no está instalado, el backup queda sin comprimir"
    fi
fi

echo ""
echo "============================================================"
echo "  ✅ BACKUP COMPLETADO"
echo "============================================================"
echo ""
echo "📁 Backup guardado en: $BACKUP_DIR"
echo ""
echo "📋 Para restaurar este backup:"
echo "   1. Detener los contenedores: docker-compose down"
echo "   2. Copiar los archivos de vuelta"
echo "   3. Iniciar los contenedores: docker-compose up -d"
echo ""
