# Mejoras y lecciones para 2008 y años anteriores

Notas acumuladas al cerrar 2009, para aplicar de entrada (no reactivamente)
en 2008 y los años que sigan hacia atrás.

## 1. El match rate de la primera pasada seguirá bajando cuanto más viejo el año

Patrón observado y ya consistente en 3 bloques sucesivos:

| Bloque | Match rate primera pasada (Haiku 5.5) |
|---|---|
| 2015-2025 | 92.8%-99.8% |
| 2010-2014 | 89.5%-93.9% |
| 2009 | 66.5% (cayendo hasta 35.3% en una de las partes) |

Causa raíz confirmada en 2009 (igual que en 2011-2014, pero más marcada):
SKUs capturados **solo con código de marca, sin descripción**. Años más
antiguos del catálogo de GS1 Venezuela tienden a tener menos texto
descriptivo. **Esperar que 2008 repita o empeore este patrón.**

## 2. No esperar a terminar el año para decidir si hace falta rescate anticipado

En vez de cerrar la primera pasada, revisar el reporte, y *luego* decidir —
aplicar el rescate anticipado (Sonnet 5.5 + heurística Marca→Segmento) de
entrada en cuanto la primera pasada esté completa, sin ciclo de
aprobación intermedio, salvo que el usuario pida lo contrario. Esto ya se
volvió el flujo estándar, no la excepción.

## 3. La heurística Marca→Segmento es el rescate más efectivo, no un parche menor

En 2009 rescató **15,179 filas** (62% de todo el residual post-Sonnet),
más que el propio Sonnet 5.5 (6,634). Confirma que para años con
convención "código de marca sin descripción", la heurística no es un
complemento — es el rescate principal. No subestimar su importancia al
estimar tiempos/costos para 2008.

## 4. Organizar `input_<año>/` ni bien lleguen los archivos, sin esperar instrucción

2008 llegó esta vez por upload directo a GitHub (no por este chat) — se
organizó en `input_2008/` en cuanto se detectó, siguiendo la convención ya
establecida. Mantener esta disciplina: cualquier archivo crudo que
aparezca en la raíz se mueve a `input_<año>/` de inmediato.

## 5. Vigilar divergencia del repo cuando hay subidas directas a GitHub

El commit de 2008 llegó directo a la rama por upload web, mientras este
mismo proceso corría en paralelo — causó un `push` rechazado (no
fast-forward). Se resolvió con un merge limpio porque no hubo archivos en
común. Si esto se repite, revisar primero qué tocó el commit remoto
(`git show --stat <commit>`) antes de mergear a ciegas.

## 6. Deuda técnica pendiente (no bloqueante, pero documentada)

Al correr `retrieve_batches.py` sobre el tracker completo, varias entradas
viejas de "rescate Sonnet 5.5" de 2015-2025 (del envío original fallido
por el bug de `thinking_config`, nunca limpiado tras el reenvío exitoso)
fallan repetidamente con "no se encuentra el archivo original" porque sus
rutas de origen cambiaron en la reorganización del repo. Es ruido inocuo
— nunca se marcan como `retrieved`, así que no corrompen nada — pero
conviene limpiarlas del `batch_tracker.json` en algún momento para que el
log deje de llenarse de advertencias irrelevantes cada vez que se corre
`retrieve_batches.py`.

## 7. Verificar la API key al inicio de cada sesión nueva

El entorno no persiste `ANTHROPIC_API_KEY` entre sesiones/contenedores.
Confirmar que esté configurada en **Network secrets** del entorno antes
de intentar cualquier envío — evita el bloqueo que ya se repitió una vez
al arrancar 2009.
