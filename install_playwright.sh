#!/bin/bash
set -e  # Detiene el script si ocurre un error

echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install playwright

echo "🌐 Instalando navegadores..."
playwright install --with-deps

echo "✅ Instalación completada con éxito."