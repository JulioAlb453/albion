"""Carga el catálogo de armas, armaduras y artefactos en la base de datos.

Desde backend/:
    python -m scripts.importar_catalogo                      # descarga items.json del volcado público
    python -m scripts.importar_catalogo --origen items.json  # o lo lee de un archivo local

Se puede repetir cuando el juego agregue objetos: reemplaza el catálogo completo.
"""

import argparse
import asyncio
import json
import os
from collections import Counter
from pathlib import Path

import httpx

from src.core.infrastructure.database import Database
from src.mercado.infrastructure.catalogo_items_json import leer_catalogo
from src.mercado.infrastructure.sqlite_catalogo_objetos import SqliteCatalogoObjetos

URL_ITEMS = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json"


async def _leer_entradas(origen: str | None) -> list[dict]:
    if origen:
        return json.loads(Path(origen).read_text(encoding="utf-8-sig"))
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as cliente:
        respuesta = await cliente.get(URL_ITEMS)
        respuesta.raise_for_status()
        return respuesta.json()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=os.environ.get("GREMIO_DB", "data/gremio.db"))
    parser.add_argument("--origen", help="items.json local; sin esto se descarga")
    argumentos = parser.parse_args()

    objetos = leer_catalogo(await _leer_entradas(argumentos.origen))
    Path(argumentos.db).parent.mkdir(parents=True, exist_ok=True)
    db = Database(argumentos.db)
    await db.abrir()
    try:
        await SqliteCatalogoObjetos(db).reemplazar(objetos)
    finally:
        await db.cerrar()

    por_categoria = Counter(objeto.categoria.value for objeto in objetos)
    print(f"{len(objetos)} objetos guardados en {argumentos.db}: {dict(por_categoria)}")


if __name__ == "__main__":
    asyncio.run(main())
