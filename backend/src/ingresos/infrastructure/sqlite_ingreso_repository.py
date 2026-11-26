from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto, a_texto_o_none, desde_texto
from src.core.infrastructure.sql import clausula_where
from src.ingresos.domain.entities.ingreso import CategoriaIngreso, Ingreso
from src.ingresos.domain.ports.i_ingreso_repository import FiltroIngresos, IIngresoRepository

_COLUMNAS = "id, categoria, descripcion, monto, fecha"


def _a_ingreso(fila: tuple) -> Ingreso:
    id_, categoria, descripcion, monto, fecha = fila
    return Ingreso(CategoriaIngreso(categoria), descripcion, monto, desde_texto(fecha), id_)


class SqliteIngresoRepository(IIngresoRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save(self, ingreso: Ingreso) -> Ingreso:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                "INSERT INTO ingresos (categoria, descripcion, monto, fecha) VALUES (?, ?, ?, ?)",
                (ingreso.categoria.value, ingreso.descripcion, ingreso.monto, a_texto(ingreso.fecha)),
            )
            ingreso.id = cursor.lastrowid
        return ingreso

    async def get_by_id(self, ingreso_id: int) -> Ingreso | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(f"SELECT {_COLUMNAS} FROM ingresos WHERE id = ?", (ingreso_id,))
            fila = await cursor.fetchone()
        return None if fila is None else _a_ingreso(fila)

    async def delete(self, ingreso_id: int) -> None:
        async with self._db.sesion() as conn:
            await conn.execute("DELETE FROM ingresos WHERE id = ?", (ingreso_id,))

    async def list(self, filtro: FiltroIngresos = FiltroIngresos()) -> list[Ingreso]:
        donde, parametros = clausula_where(
            [
                ("fecha >= ?", a_texto_o_none(filtro.desde)),
                ("fecha <= ?", a_texto_o_none(filtro.hasta)),
                ("categoria = ?", filtro.categoria and filtro.categoria.value),
            ]
        )
        async with self._db.sesion() as conn:
            cursor = await conn.execute(f"SELECT {_COLUMNAS} FROM ingresos {donde} ORDER BY fecha, id", parametros)
            filas = await cursor.fetchall()
        return [_a_ingreso(fila) for fila in filas]
