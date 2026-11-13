#!/usr/bin/env python3
"""Arranca el servidor y abre el navegador SOLO cuando ya responde.

Evita la "carrera" entre abrir el navegador y que uvicorn termine de
importar todo (pandas, scikit-learn, etc. pueden tardar hasta un
minuto la primera vez en una PC normal) -- sin esto, el navegador
muestra "conexión rechazada" aunque el servidor sí vaya a arrancar bien
unos segundos después.
"""
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"
TIMEOUT_SEGUNDOS = 90


def servidor_listo() -> bool:
    try:
        urllib.request.urlopen(f"{URL}/api/paises", timeout=1)
        return True
    except (urllib.error.URLError, ConnectionError, OSError):
        return False


def main() -> int:
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", HOST, "--port", str(PORT)]
    )

    print(f"\nCargando el catálogo GPC... puede tardar hasta un minuto la primera vez.")
    inicio = time.time()
    abierto = False
    try:
        while time.time() - inicio < TIMEOUT_SEGUNDOS:
            if proceso.poll() is not None:
                print("\nERROR: el servidor se cerró inesperadamente. Revisa los mensajes de arriba.")
                return 1
            if servidor_listo():
                if not abierto:
                    print("Listo — abriendo la app en tu navegador...\n")
                    webbrowser.open(URL)
                    abierto = True
                break
            time.sleep(0.5)
        else:
            print(
                "\nEl servidor está tardando más de lo normal. Revisa los mensajes de arriba "
                f"por si hay un error, o abre {URL} manualmente en tu navegador en unos segundos."
            )

        print("NO CIERRES ESTA VENTANA mientras uses la app.")
        print("Para cerrar la app, cierra esta ventana o presiona Ctrl+C.\n")
        proceso.wait()
    except KeyboardInterrupt:
        proceso.terminate()
    return proceso.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
