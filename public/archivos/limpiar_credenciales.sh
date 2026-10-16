#!/bin/bash
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
grep -rn "password.*=.*['\"]" --include="*.py" . | grep -v "os.environ"
grep -rn "webhook" --include="*.py" . -i

echo ""
echo "⚠️  Si ves líneas arriba, hay credenciales expuestas."
echo ""

# 2. Crear .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo "✅ Archivo .env creado. Editá las variables con tus datos reales:"
    echo "   nano .env"
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
echo "✅ Limpieza completada"
