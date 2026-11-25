from decimal import Decimal

from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.domain.ports.i_seguimiento_repository import ISeguimientoRepository
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.infrastructure.database import Database

_COLUMNAS = (
    "id, base_id, encantamiento, calidad, ciudad_referencia, porcentaje_minimo, neto_minimo, activo"
)


def _a_seguimiento(fila: tuple) -> Seguimiento:
    id_, base_id, encantamiento, calidad, ciudad, porcentaje, neto_minimo, activo = fila
    return Seguimiento(
        objeto=ObjetoRef(base_id, encantamiento, Calidad(calidad)),
        ciudad_referencia=Ciudad(ciudad),
        porcentaje_minimo=None if porcentaje is None else Decimal(porcentaje),
        neto_minimo=neto_minimo,
        activo=bool(activo),
        id=id_,
    )


class SqliteSeguimientoRepository(ISeguimientoRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save(self, seguimiento: Seguimiento) -> Seguimiento:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"INSERT INTO seguimientos ({_COLUMNAS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT (id) DO UPDATE SET "
                "base_id = excluded.base_id, encantamiento = excluded.encantamiento, "
                "calidad = excluded.calidad, ciudad_referencia = excluded.ciudad_referencia, "
                "porcentaje_minimo = excluded.porcentaje_minimo, "
                "neto_minimo = excluded.neto_minimo, activo = excluded.activo",
                (
                    seguimiento.id, seguimiento.objeto.base_id, seguimiento.objeto.encantamiento,
                    int(seguimiento.objeto.calidad), seguimiento.ciudad_referencia.value,
                    None if seguimiento.porcentaje_minimo is None else str(seguimiento.porcentaje_minimo),
                    seguimiento.neto_minimo, int(seguimiento.activo),
                ),
            )
            if seguimiento.id is None:
                seguimiento.id = cursor.lastrowid
        return seguimiento

    async def get_by_id(self, seguimiento_id: int) -> Seguimiento | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM seguimientos WHERE id = ?", (seguimiento_id,)
            )
            fila = await cursor.fetchone()
        return None if fila is None else _a_seguimiento(fila)

    async def list_activos(self) -> list[Seguimiento]:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM seguimientos WHERE activo = 1 ORDER BY id"
            )
            filas = await cursor.fetchall()
        return [_a_seguimiento(fila) for fila in filas]

    async def delete(self, seguimiento_id: int) -> None:
        async with self._db.sesion() as conn:
            await conn.execute("DELETE FROM seguimientos WHERE id = ?", (seguimiento_id,))
