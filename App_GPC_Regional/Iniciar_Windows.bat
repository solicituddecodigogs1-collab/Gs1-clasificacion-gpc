@echo off
setlocal enabledelayedexpansion
title Clasificacion GPC - GS1 LatAm
cd /d "%~dp0"

echo ============================================================
echo   Clasificacion GPC - GS1 LatAm
echo ============================================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    set PY=python
) else (
    where py >nul 2>nul
    if !errorlevel!==0 (
        set PY=py
    ) else (
        echo No se encontro Python instalado en esta computadora.
        echo.
        echo Para usar esta app necesitas instalar Python primero:
        echo   1. Ve a https://www.python.org/downloads/
        echo   2. Descarga e instala la version para Windows.
        echo   3. IMPORTANTE: durante la instalacion, marca la casilla
        echo      "Add python.exe to PATH".
        echo   4. Vuelve a ejecutar este archivo.
        echo.
        pause
        exit /b 1
    )
)

if not exist ".venv" (
    echo Preparando la app por primera vez, puede tardar 1-2 minutos...
    %PY% -m venv .venv
    if not exist ".venv" (
        echo No se pudo crear el entorno. Revisa que Python este bien instalado.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

python -c "import fastapi" >nul 2>nul
if not %errorlevel%==0 (
    echo Instalando dependencias, puede tardar unos minutos...
    pip install -q -r requirements.txt
)

echo.
echo Abriendo la app en tu navegador...
start "" http://localhost:8000
echo.
echo NO CIERRES ESTA VENTANA mientras uses la app.
echo Para cerrar la app, cierra esta ventana o presiona Ctrl+C.
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
