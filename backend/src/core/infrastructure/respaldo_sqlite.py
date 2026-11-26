import logging
import os
import re
from pathlib import Path

from src.core.domain.ports.i_reloj import IReloj
from src.core.infrastructure.database import Database

_NOMBRE = re.compile(r"^gremio-\d{4}-\d{2}-\d{2}\.db$")
_registro = logging.getLogger("gremio.respaldo")


class RespaldoSqlite:
    """Una copia de la base por día (hora UTC), conservando las más recientes.

    Usa `VACUUM INTO`, que copia una instantánea consistente aunque la base esté en uso. La
    copia se escribe con nombre temporal y se renombra al terminar: si se apaga la PC a la
    mitad, no queda una copia rota con nombre de buena. Solo toca archivos `gremio-AAAA-MM-DD.db`.
    """

    def __init__(self, db: Database, carpeta: Path, reloj: IReloj, conservar: int):
        self._db = db
        self._carpeta = carpeta
        self._reloj = reloj
        self._conservar = conservar

    async def ejecutar(self) -> Path | None:
        """La ruta de la copia nueva, o None si ya había una de hoy."""
        self._carpeta.mkdir(parents=True, exist_ok=True)
        destino = self._carpeta / f"gremio-{self._reloj.ahora():%Y-%m-%d}.db"
        if destino.exists():
            return None
        temporal = destino.with_name(destino.name + ".tmp")
        temporal.unlink(missing_ok=True)  # resto de un corte anterior
        async with self._db.sesion() as conn:
            await conn.execute("VACUUM INTO ?", (str(temporal),))
        os.replace(temporal, destino)
        self._podar()
        _registro.info("Copia de seguridad creada: %s", destino)
        return destino

    def _podar(self) -> None:
        copias = sorted(p for p in self._carpeta.iterdir() if _NOMBRE.match(p.name))
        for vieja in copias[: max(0, len(copias) - self._conservar)]:
            vieja.unlink(missing_ok=True)
