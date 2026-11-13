@echo off
setlocal enabledelayedexpansion
title Clasificacion GPC - GS1 LatAm
cd /d "%~dp0"

echo ============================================================
echo   Clasificacion GPC - GS1 LatAm
echo ============================================================
echo.

if not exist "requirements.txt" goto :carpeta_incompleta
if not exist "backend\main.py" goto :carpeta_incompleta
if not exist "frontend\index.html" goto :carpeta_incompleta
goto :carpeta_ok

:carpeta_incompleta
echo ERROR: Falta descargar la carpeta completa.
echo.
echo Este archivo debe estar DENTRO de la carpeta App_GPC_Regional
echo completa (junto con las carpetas "backend" y "frontend" y el
echo archivo "requirements.txt"). Parece que solo se descargo este
echo archivo .bat suelto, sin el resto de la carpeta.
echo.
echo Como descargar la carpeta completa:
echo   1. Ve al repositorio en GitHub, en la rama correcta.
echo   2. Boton verde "Code" -^> "Download ZIP".
echo   3. Descomprime el ZIP completo (no copies solo este archivo).
echo   4. Entra a la carpeta App_GPC_Regional dentro de lo que
echo      descomprimiste, y desde ahi haz doble clic en este archivo.
echo.
pause
exit /b 1

:carpeta_ok
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

python -c "import fastapi, uvicorn" >nul 2>nul
if not %errorlevel%==0 (
    echo Instalando dependencias, puede tardar unos minutos...
    pip install -q -r requirements.txt
)

python -c "import fastapi, uvicorn" >nul 2>nul
if not %errorlevel%==0 (
    echo.
    echo ERROR: No se pudieron instalar las dependencias.
    echo Revisa que tengas conexion a internet e intenta de nuevo.
    echo Si el problema sigue, copia el mensaje de arriba y pide ayuda.
    echo.
    pause
    exit /b 1
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
