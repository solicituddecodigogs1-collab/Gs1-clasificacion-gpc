# App de clasificación GPC — GS1 LatAm

Interfaz web (Streamlit) para que cualquier MO de GS1 en la región suba su
catálogo, clasifique sus productos bajo GPC con Claude, y descargue el
resultado — usando su propia API key de Anthropic (cada MO paga su propio
uso; GS1 Venezuela no factura nada).

Reutiliza la lógica ya probada en `lib/submit_batches.py` del repo
principal (el mismo catálogo oficial, el mismo system prompt, la misma
selección de candidatos) — esto es una interfaz encima de esa lógica, no
una reimplementación.

## Estado: primera versión funcional (MVP)

Probado: la app carga sin errores, el flujo de crear proyecto y elegir
país funciona (`streamlit.testing.v1.AppTest`). **No probado de punta a
punta con una API key real** — antes de dárselo a una MO, correr el flujo
completo una vez con una cuenta de prueba, con un catálogo chico (20-30
filas), para confirmar que el envío y la descarga de resultados del Batch
API funcionan como se espera en este SDK/versión de Anthropic.

## Cómo correrla

```bash
cd App_GPC_Regional
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501`. Cada proyecto se identifica con un código
corto (ej. `A1B2C3`) que se genera al crear uno nuevo — guárdalo para
volver más tarde, porque los batches de la API pueden tardar horas.

## Qué hace, paso a paso

1. **País** (barra lateral): elige tu MO de una lista de 19 países de
   LatAm. Muestra el prefijo GS1 de referencia y el nombre del
   identificador fiscal local (solo informativo). Puedes agregar tus
   propias notas de jerga/abreviaturas de tu catálogo — se le añaden al
   system prompt del modelo.
2. **API key**: la pegas en la barra lateral. Vive solo en memoria de esa
   sesión del navegador — nunca se escribe a disco.
3. **Subir catálogo**: `.xlsx` o `.csv`, y mapeas qué columna es marca,
   cuál es descripción y cuál es el identificador único.
4. **Estimar costo**: antes de gastar un centavo, te muestra cuántos
   productos únicos hay (tras deduplicar) y el costo proyectado.
5. **Pasada 1 (Haiku)**: envía el lote a la Batch API, te da el ID del
   batch, puedes verificar el estado cuando quieras (o cerrar la pestaña
   y volver luego con tu código de proyecto).
6. **Pasada 2 (Sonnet)**: rescate automático de lo que Haiku dejó en
   `NO_MATCH`, mismo patrón de envío/espera/descarga.
7. **Descarga**: tres archivos — el completo, solo los asignados, solo
   los `NO_MATCH` — listos para revisar.

## Qué falta / limitaciones conocidas

- **Prefijos GS1 por país**: varios están marcados "revisar" en
  `paises.py` — vienen del conocimiento general del modelo, no de una
  verificación directa contra gs1.org/prefixes (el sitio bloqueó el
  fetch automático al momento de construir esto). Son solo informativos
  en la interfaz, no afectan la clasificación — pero conviene corregirlos
  antes de mostrarle la app a una MO.
- **Sin autenticación ni multiusuario real**: cualquiera con la URL y un
  código de proyecto puede ver/continuar ese proyecto. Suficiente para un
  piloto interno; no para una app pública sin control de acceso.
- **Sin reintentos automáticos** si la llamada a la Batch API falla a
  mitad de camino (ej. red cortada). Si algo falla, hay que repetir ese
  paso manualmente.
- **Hosting**: esto corre local o en cualquier servidor que instale
  Python — no está desplegado en ningún lugar público todavía. Falta
  decidir dónde y quién lo mantiene (ver conversación con GS1 Venezuela
  sobre esto).
