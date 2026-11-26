"""Carga en la base de datos el catálogo de todo lo que se vende en el mercado.

Desde backend/:
    python -m scripts.importar_catalogo                  # descarga los dos items.json del volcado público
    python -m scripts.importar_catalogo --origen carpeta # o los lee de una carpeta local:
                                                         #   carpeta/items.json y carpeta/formatted/items.json

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

_VOLCADO = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master"
ARCHIVOS = ("items.json", "formatted/items.json")  # datos de cada objeto, y sus nombres


async def _leer_volcado(origen: str | None) -> list:
    if origen:
        return [json.loads((Path(origen) / archivo).read_text(encoding="utf-8-sig")) for archivo in ARCHIVOS]
    async with httpx.AsyncClient(timeout=180, follow_redirects=True) as cliente:
        contenidos = []
        for archivo in ARCHIVOS:
            respuesta = await cliente.get(f"{_VOLCADO}/{archivo}")
            respuesta.raise_for_status()
            contenidos.append(json.loads(respuesta.content.decode("utf-8-sig")))
        return contenidos


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=os.environ.get("GREMIO_DB", "data/gremio.db"))
    parser.add_argument("--origen", help="carpeta con items.json y formatted/items.json; sin esto se descargan")
    argumentos = parser.parse_args()

    datos, nombres = await _leer_volcado(argumentos.origen)
    objetos = leer_catalogo(datos, nombres)
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
