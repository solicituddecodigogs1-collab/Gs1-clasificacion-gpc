# App de clasificación GPC — GS1 LatAm

Interfaz web (HTML/CSS/JS propio + backend FastAPI) para que cualquier MO de GS1
en la región suba su catálogo, clasifique sus productos bajo GPC con Claude, y
descargue el resultado — usando su propia API key de Anthropic (cada MO paga su
propio uso; GS1 Venezuela no factura nada).

Reutiliza la lógica ya probada en `lib/submit_batches.py` del repo principal (el
mismo catálogo oficial, el mismo system prompt, la misma selección de
candidatos) — esto es una interfaz encima de esa lógica, no una reimplementación.

## Por qué no es un sitio 100% estático

Se evaluó armarla 100% client-side (sin servidor), llamando a la Batch API de
Anthropic directo desde el navegador. Es técnicamente posible (Anthropic lo
permite con `dangerouslyAllowBrowser`), pero se decidió mantener un backend
Python liviano porque:

- Reutiliza tal cual la búsqueda de candidatos del catálogo (TF-IDF con
  scikit-learn, 5.318 bricks) — reimplementarla en JavaScript es trabajo real
  y duplica lógica que ya está probada.
- Permite guardar el progreso del proyecto en el servidor por un código corto,
  para poder cerrar el navegador y volver después desde cualquier equipo — los
  batches pueden tardar horas. Un sitio 100% estático solo puede guardar eso en
  el navegador de esa persona (`localStorage`), atado a ese equipo.

El frontend (`frontend/`) es HTML/CSS/JS plano, sin build step ni framework —
cualquiera puede abrir y editar esos archivos directamente.

## Estado: primera versión funcional (MVP)

**Probado de punta a punta con `playwright`** hasta donde no requiere una API
key real: crear proyecto, elegir país (con el detalle de prefijo GS1 + ID
fiscal), pegar la key, subir un catálogo de prueba, mapear columnas (con
preview de datos), ver la estimación de costo, y retomar un proyecto ya
terminado por su código. Las capturas de cada pantalla se revisaron
visualmente.

**No probado con una API key real** — antes de dárselo a una MO, correr el
flujo completo una vez con una cuenta de prueba y un catálogo chico (20-30
filas), para confirmar que el envío y la descarga de resultados del Batch API
de Anthropic funcionan como se espera en este SDK/versión.

## Cómo correrla

### Opción fácil — un solo doble clic (recomendada para una MO sin conocimientos técnicos)

1. Descarga o clona esta carpeta (`App_GPC_Regional/`) completa.
2. **Windows:** doble clic en `Iniciar_Windows.bat`.
   **Mac / Linux:** doble clic en `Iniciar_Mac_Linux.sh` (si no abre al hacer
   doble clic, clic derecho → Abrir con → Terminal, o desde una terminal:
   `./Iniciar_Mac_Linux.sh`).
3. La primera vez tarda 1-2 minutos preparando todo (instala lo necesario
   solo, sin que el usuario haga nada más). Las siguientes veces arranca en
   segundos.
4. Se abre sola en el navegador en `http://localhost:8000`. Para cerrar la
   app, se cierra esa ventana de la terminal.

Si la computadora no tiene Python instalado, el script lo detecta y explica
cómo instalarlo (un paso único, de una sola vez).

### Opción manual (para quien prefiera la terminal)

```bash
cd App_GPC_Regional
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Sobre el código de proyecto

Cada proyecto se identifica con un código corto (ej. `A1B2C3`) que se genera
al crear uno nuevo — se guarda en el navegador (`localStorage`) y también se
puede volver a ingresar manualmente desde otro equipo, porque el estado vive
en el servidor (`.proyectos/<código>/`), no solo en el navegador.

## Qué hace, paso a paso

1. **País**: eliges tu MO de una grilla de 19 países de LatAm. Muestra el
   prefijo GS1 de referencia y el nombre del identificador fiscal local (solo
   informativo). Puedes agregar tus propias notas de jerga/abreviaturas de tu
   catálogo — se le añaden al system prompt del modelo.
2. **API key**: la pegas una vez por sesión de navegador. Viaja al backend
   solo en el header de cada request que la necesita — nunca se escribe a
   disco ni se registra en logs.
3. **Subir catálogo**: `.xlsx` o `.csv`, arrastrar y soltar o seleccionar
   archivo. Mapeas qué columna es marca, cuál es descripción y cuál es el
   identificador único, con preview de las primeras filas.
4. **Estimar costo**: antes de gastar un centavo, muestra cuántos productos
   únicos hay (tras deduplicar) y el costo proyectado.
5. **Pasada 1 (Haiku)**: envía el lote a la Batch API, puedes verificar el
   estado cuando quieras (o cerrar la pestaña y volver luego con tu código).
6. **Pasada 2 (Sonnet)**: rescate automático de lo que Haiku dejó en
   `NO_MATCH`, mismo patrón de envío/espera/descarga. Se puede saltar.
7. **Descarga**: tres archivos — el completo, solo los asignados, solo los
   `NO_MATCH` — listos para revisar.

## Estructura

```
App_GPC_Regional/
├── Iniciar_Windows.bat    (doble clic para arrancar en Windows, sin terminal)
├── Iniciar_Mac_Linux.sh   (doble clic / ./Iniciar_Mac_Linux.sh en Mac o Linux)
├── backend/
│   ├── main.py       (API FastAPI: todos los endpoints)
│   ├── core.py        (lógica del pipeline, sin interfaz — reusa lib/submit_batches.py)
│   └── paises.py      (configuración de los 19 países)
├── frontend/
│   ├── index.html     (las 12 pantallas del flujo, mostradas/ocultadas por JS)
│   ├── style.css       (paleta GS1: navy + naranja, sin framework de CSS)
│   └── app.js          (llama a la API, maneja el estado del navegador)
└── requirements.txt
```

## Qué falta / limitaciones conocidas

- **Prefijos GS1 por país**: varios están marcados "revisar" en
  `backend/paises.py` — vienen del conocimiento general del modelo, no de una
  verificación directa contra gs1.org/prefixes. Son solo informativos en la
  interfaz, no afectan la clasificación — pero conviene corregirlos antes de
  mostrarle la app a una MO.
- **Sin autenticación ni multiusuario real**: cualquiera con la URL y un
  código de proyecto puede ver/continuar ese proyecto. Suficiente para un
  piloto interno; no para una app pública sin control de acceso.
- **Pensada para uso en computadora** — no se adaptó el diseño a pantallas de
  celular (decisión explícita, no es el caso de uso).
- **Sin reintentos automáticos** si la llamada a la Batch API falla a mitad de
  camino (ej. red cortada). Si algo falla, hay que repetir ese paso
  manualmente.
- **Hosting**: esto corre local o en cualquier servidor que instale Python —
  no está desplegado en ningún lugar público todavía. Falta decidir dónde y
  quién lo mantiene.
