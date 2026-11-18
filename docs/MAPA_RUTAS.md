# Mapa de rutas: estructura anterior → actual

Reorganización hecha con `git mv`: `git log --follow <archivo>` conserva el historial.

| Antes | Ahora |
|---|---|
| `Input_Historico/<año>/*` (1993-2004) | `datos/entrada/<año>/` |
| `Output_Clasificado/Archivo_*/input_<año>/*` (2005-2025) | `datos/entrada/<año>/` |
| `Output_Historico/Final_<año>.xlsx` | `datos/final/` |
| `Final_2011..2025.xlsx` (raíz) | **eliminados**: eran copias idénticas (byte a byte) de `datos/final/Final_<año>.xlsx`; siguen en el historial de git |
| `Final_2010.xlsx` (raíz) | `datos/final/_revisar/Final_2010_version_raiz.xlsx` (difiere del canónico) |
| `Output_Asignados/` | `datos/asignados/` |
| `Output_NoMatch/` | `datos/no_match/extraido/` |
| `no_match_historico/` + `Output_Clasificado/Archivo_*/no_match_historico/` | `datos/no_match/historico/` |
| `no_match_residual/` + `Output_Clasificado/Archivo_*/no_match_residual/` | `datos/no_match/residual/` |
| `Remanentes_NO_MATCH/` | `datos/no_match/remanentes/` |
| `Output_Clasificado/NoMatch_Clasificado/` | `datos/no_match/clasificado/` |
| `NO_MATCH_<año>_CLASIFICADO.xlsx` (raíz, 2010-2025) | `datos/no_match/clasificado/` |
| `Output_Clasificado/**/no_match_<año>_{rescate_sonnet,reprocesado_haiku55}.xlsx` | `datos/salida/` |
| `Output_Clasificado/` (directorio de trabajo) | `datos/salida/` |
| `Output_SinHeuristica/` | `datos/sin_heuristica/` |
| `archivo_piloto/` | `datos/piloto/` |
| `informes/informe_final_1993_2025.xlsx` | `docs/informes/` |
| `MEJORAS_ANIOS_SIGUIENTES.md` | `docs/` |
| `Asamblea_General_GS1_Venezuela_2026*.pptx` (raíz) | `docs/presentaciones/` |
| `scripts/rescate_anticipado_*.py` | `scripts/rescate_anticipado/` |
| `herramientas/reprocess_*.py`, `resubmit_2019_haiku55.py` | `herramientas/reprocesos_puntuales/` |

Se actualizaron las constantes de ruta (`Path("...")`, docstrings) de `lib/`, `scripts/` y
`herramientas/`, y los `sys.path` de los scripts que bajaron un nivel. `App_GPC_Regional/` y
`Paquete_Replicacion_MO/` no se modificaron.
