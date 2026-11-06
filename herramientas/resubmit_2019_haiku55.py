#!/usr/bin/env python3
"""Reenvía las 5 partes de 2019 completas a la Batch API bajo el nuevo
modelo (claude-haiku-5-5), ignorando el guard de already_submitted() de
submit_batches.py (que normalmente evita duplicar un envío si ya existe
una entrada activa en el tracker para ese source_file) — aquí el
reprocesamiento completo es intencional por pedido explícito del usuario,
no un reenvío accidental.

Reutiliza las funciones reales de submit_batches.py (load_sample,
build_request_dicts, write_jsonl_temp, read_jsonl_as_requests) para que
el comportamiento sea idéntico a una corrida normal del pipeline; solo
el guard de "ya existe" se evita pasando un tracker vacío a
submit_batch_for_file(), mientras que el tracker real se actualiza y
guarda normalmente.
"""

import logging
import sys

import submit_batches as sb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("resubmit_2019_haiku55")

TARGET_FILES = [f"input_2019/2019 Consolidado_Parte_{i}.xlsx" for i in range(1, 6)]


def main() -> int:
    import anthropic

    try:
        catalog = sb.GpcCatalog(sb.CATALOG_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    client = anthropic.Anthropic()
    real_tracker = sb.load_tracker()

    for file_path in TARGET_FILES:
        file_name = sb.Path(file_path).name
        # already_submitted() bloquearía esto porque ya existen entradas
        # "ended" para estos 5 archivos (el reprocesamiento es intencional,
        # no un reenvío accidental) — se le pasa una vista del tracker SIN
        # las entradas previas de este archivo solo para ese chequeo; la
        # entrada nueva que agregue se vuelca de inmediato al tracker real.
        filtered_view = [e for e in real_tracker if e.get("source_file") != file_name]
        before = len(filtered_view)
        sb.submit_batch_for_file(client, file_path, filtered_view, catalog)
        new_entries = filtered_view[before:]
        real_tracker.extend(new_entries)
        sb.save_tracker(real_tracker)

    logger.info("Reenvío de las 5 partes de 2019 (Haiku 5.5) finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
