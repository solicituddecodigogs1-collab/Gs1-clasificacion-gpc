#!/usr/bin/env python3
"""Envía los 11 archivos de no_match_historico/ (años 2015-2025) a la
Batch API bajo submit_batches_rescate.py (Sonnet 5.5 + regla de rescate),
ignorando el guard de already_submitted() de submit_batches_rescate.py
(que normalmente evita duplicar un envío si ya existe una entrada activa
en el tracker para ese source_file) — aquí ya existe una entrada previa
por archivo (de la ronda de rescate con Haiku 5.5), pero este envío es
intencional, bajo un modelo y prompt distintos.

Reutiliza submit_batch_for_file de submit_batches_rescate.py sin
modificarlo; solo el guard de "ya existe" se evita pasando un tracker
filtrado, mientras que el tracker real se actualiza y guarda normalmente,
con el source_file original (sin sufijo) para que retrieve_rescate_sonnet.py
pueda encontrar la entrada más reciente por archivo.
"""

import logging
import sys
from pathlib import Path

import submit_batches_rescate as sbr

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("resubmit_rescate_sonnet")

NO_MATCH_DIR = Path("no_match_historico")


def main() -> int:
    import anthropic

    try:
        catalog = sbr.GpcCatalog(sbr.CATALOG_FILE)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        return 1

    client = anthropic.Anthropic()
    real_tracker = sbr.load_tracker()

    files = sorted(NO_MATCH_DIR.glob("no_match_*.xlsx"))
    logger.info(f"Se procesarán {len(files)} archivo(s): {[f.name for f in files]}")

    for file_path in files:
        file_name = file_path.name
        filtered_view = [e for e in real_tracker if e.get("source_file") != file_name]
        before = len(filtered_view)
        sbr.submit_batch_for_file(client, str(file_path), filtered_view, catalog)
        new_entries = filtered_view[before:]
        # Igual que otras rondas de reprocesamiento en este repo: se marca
        # el source_file con un sufijo distintivo para no confundir esta
        # entrada con la de la ronda de rescate anterior (Haiku 5.5) del
        # mismo archivo en batch_tracker.json.
        for entry in new_entries:
            entry["source_file"] = f"{file_name} (rescate Sonnet 5.5)"
        real_tracker.extend(new_entries)
        sbr.save_tracker(real_tracker)

    logger.info("Envío de rescate Sonnet 5.5 finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
