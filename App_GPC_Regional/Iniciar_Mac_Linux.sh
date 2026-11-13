#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  Clasificación GPC — GS1 LatAm"
echo "============================================================"
echo

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

if ! python -c "import fastapi" >/dev/null 2>&1; then
  echo "Instalando dependencias, puede tardar unos minutos..."
  pip install -q -r requirements.txt
fi

echo
echo "Abriendo la app en tu navegador..."
( sleep 2
  if command -v open >/dev/null 2>&1; then open http://localhost:8000
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:8000
  fi
) &

echo
echo "NO CIERRES ESTA VENTANA mientras uses la app."
echo "Para cerrar la app, presiona Ctrl+C."
echo

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
