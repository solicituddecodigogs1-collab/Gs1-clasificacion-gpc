#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  Clasificación GPC — GS1 LatAm"
echo "============================================================"
echo

if [ ! -f "requirements.txt" ] || [ ! -f "backend/main.py" ] || [ ! -f "frontend/index.html" ]; then
  echo "ERROR: Falta descargar la carpeta completa."
  echo
  echo "Este archivo debe estar DENTRO de la carpeta App_GPC_Regional"
  echo "completa (junto con las carpetas backend/ y frontend/ y el"
  echo "archivo requirements.txt). Parece que solo se descargó este"
  echo "archivo .sh suelto, sin el resto de la carpeta."
  echo
  echo "Cómo descargar la carpeta completa:"
  echo "  1. Ve al repositorio en GitHub, en la rama correcta."
  echo "  2. Botón verde 'Code' -> 'Download ZIP'."
  echo "  3. Descomprime el ZIP completo (no copies solo este archivo)."
  echo "  4. Entra a la carpeta App_GPC_Regional dentro de lo que"
  echo "     descomprimiste, y desde ahí corre este archivo."
  echo
  read -p "Presiona Enter para cerrar..."
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "No se encontró Python instalado en esta computadora."
  echo
  echo "Para usar esta app necesitas instalar Python primero:"
  echo "  macOS:  brew install python3   (o desde https://www.python.org/downloads/)"
  echo "  Linux:  sudo apt install python3 python3-venv   (Ubuntu/Debian)"
  echo
  read -p "Presiona Enter para cerrar..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Preparando la app por primera vez, puede tardar 1-2 minutos..."
  "$PY" -m venv .venv
fi

source .venv/bin/activate

if ! python -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Instalando dependencias, puede tardar unos minutos..."
  pip install -q -r requirements.txt
fi

if ! python -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo
  echo "ERROR: No se pudieron instalar las dependencias."
  echo "Revisa que tengas conexión a internet e intenta de nuevo."
  read -p "Presiona Enter para cerrar..."
  exit 1
fi

python run_app.py
