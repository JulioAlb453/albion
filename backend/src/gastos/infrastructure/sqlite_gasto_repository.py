from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto, a_texto_o_none, desde_texto
from src.core.infrastructure.sql import clausula_where
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos, IGastoRepository

_COLUMNAS = "id, categoria, descripcion, monto, fecha"


def _a_gasto(fila: tuple) -> Gasto:
    id_, categoria, descripcion, monto, fecha = fila
    return Gasto(CategoriaGasto(categoria), descripcion, monto, desde_texto(fecha), id_)


async def _insertar(conn, gasto: Gasto) -> int:
    cursor = await conn.execute(
        "INSERT INTO gastos (categoria, descripcion, monto, fecha) VALUES (?, ?, ?, ?)",
        (gasto.categoria.value, gasto.descripcion, gasto.monto, a_texto(gasto.fecha)),
    )
    return cursor.lastrowid


class SqliteGastoRepository(IGastoRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save(self, gasto: Gasto) -> Gasto:
        async with self._db.sesion() as conn:
            gasto.id = await _insertar(conn, gasto)
        return gasto

    async def save_many(self, gastos: list[Gasto]) -> list[Gasto]:
        async with self._db.sesion() as conn:
            ids = [await _insertar(conn, gasto) for gasto in gastos]
        # Los ids se asignan al final: si el lote se deshace, ningún gasto queda con uno ajeno.
        for gasto, id_ in zip(gastos, ids):
            gasto.id = id_
        return gastos

    async def get_by_id(self, gasto_id: int) -> Gasto | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(f"SELECT {_COLUMNAS} FROM gastos WHERE id = ?", (gasto_id,))
            fila = await cursor.fetchone()
        return None if fila is None else _a_gasto(fila)

    async def delete(self, gasto_id: int) -> None:
        async with self._db.sesion() as conn:
            await conn.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))

    async def list(self, filtro: FiltroGastos = FiltroGastos()) -> list[Gasto]:
        donde, parametros = clausula_where(
            [
                ("fecha >= ?", a_texto_o_none(filtro.desde)),
                ("fecha <= ?", a_texto_o_none(filtro.hasta)),
                ("categoria = ?", filtro.categoria and filtro.categoria.value),
            ]
        )
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM gastos {donde} ORDER BY fecha, id", parametros
            )
            filas = await cursor.fetchall()
        return [_a_gasto(fila) for fila in filas]
