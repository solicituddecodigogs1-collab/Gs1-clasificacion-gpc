# Conversaciones y ramas: dónde quedó cada cosa

Todas las ramas `claude/*` del repo se revisaron comparando contenido (hash de cada archivo) contra el
historial actual. Lo que ya estaba no se duplicó; lo único se integró así:

| Conversación | Rama | Qué aportó | Dónde está ahora |
|---|---|---|---|
| GPC product classification batch scripts | `gpc-classification-batch-scripts-wl3hde` | Pipeline GPC completo 1993-2025 | Base del repo (sin trabajo pendiente) |
| Configuración clasificación GPC (sept-2026) | `gpc-classification-gs1-venezuela-i9erei` | Scripts de "Nueva Carga", orquestador `run_batch_gpc.py`, primera corrida 2024 | `scripts/nueva_carga/`, `datos/piloto/output_2024/` |
| GPC clasificación histórica 1993-2007 | `wonderful-bohr-i6stoh` | `NO_MATCH` 1993-2007 clasificado | Ya integrado antes (`datos/no_match/clasificado/`) |
| Organizar repo en carpeta insights | `great-ride-s46u2v` | Boletín interactivo, video, tablas, `analisis_regional.py`, `NO_MATCH_2008/2009_CLASIFICADO` | Merge real (historial conservado): `analisis/`, `herramientas/`, `datos/no_match/clasificado/` |
| GS1 Healthcare presentation architect | `intelligent-curie-of1nih`, `magical-rubin-58xb97` | Decks y minuta del Comité Salud (v1-v6), fuentes JS/HTML, generador python-pptx, comando `/pptx-gs1` | `docs/presentaciones/comite_salud_gs1/`, `herramientas/presentaciones/`, `.claude/commands/` |
| Proceso sello Coninverde GS1 | `inspiring-davinci-c56kan` | Versión de la presentación de la Asamblea con láminas 8 y 14 actualizadas | Merge real: `docs/presentaciones/Asamblea_..._actualizada_coninverde.pptx` |
| Manual de procedimientos contables | `cool-heisenberg-if7ivc` | Manual de cuentas por pagar | Merge real: `docs/administracion/` |
| Organización del repositorio | `blissful-gauss-xqzpb1` | Esta reorganización | — |

## Decisiones de integración

- **`insights/<año>/`** (copias por año de `Final_` y `NO_MATCH_..._CLASIFICADO` de la conversación del boletín)
  se descartó: 1994-2009 eran duplicados o versiones anteriores de `datos/final/` (1993-1999 con `NO_MATCH`
  sin resolver) y 2010-2025 eran los mismos archivos que ya están en `datos/`. `analisis_regional.py` se
  adaptó para leer de `datos/`.
- **Tres versiones de la presentación de la Asamblea** conviven en `docs/presentaciones/`
  (`(2)`, `_actualizada` y `_actualizada_coninverde`); no hay forma de saber desde git cuál es la definitiva.

## No se importó (sigue disponible en su rama)

- `clasificado_Consolidado_2010..2014_Parte_N.xlsx` de `intelligent-curie`/`magical-rubin`: partes intermedias
  cuyo contenido es idéntico a `datos/final/Final_2010..2014.xlsx` (verificado en 2010: mismas filas y mismo `gpc_code`).
- Versiones anteriores de `submit_batches*.py`, `retrieve_batches.py` y `batch_tracker.json`: `lib/` y el
  tracker actual las reemplazan.
- `.claude/skills/sports-betting-analyzer` y `skills-lock.json` (`vibrant-babbage-yd7u65`, conversación
  "Commit de uso estatico"): no tienen relación con GS1; no se mezclan con este repo.
