import dataclasses
from datetime import date

from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto_o_none, desde_texto
from src.core.infrastructure.sql import clausula_where
from src.pagos.domain.entities.pago_semanal import PagoSemanal
from src.pagos.domain.ports.i_pago_semanal_repository import FiltroPagos, IPagoSemanalRepository

_COLUMNAS = "id, miembro, monto, semana, descripcion, pagado, fecha_pago"


def _a_pago(fila: tuple) -> PagoSemanal:
    id_, miembro, monto, semana, descripcion, pagado, fecha_pago = fila
    return PagoSemanal(
        miembro, monto, date.fromisoformat(semana), descripcion, pagado,
        desde_texto(fecha_pago) if fecha_pago else None, id_,
    )


class SqlitePagoSemanalRepository(IPagoSemanalRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save(self, pago: PagoSemanal) -> PagoSemanal:
        valores = (
            pago.miembro, pago.monto, pago.semana.isoformat(), pago.descripcion, pago.pagado,
            a_texto_o_none(pago.fecha_pago),
        )
        async with self._db.sesion() as conn:
            if pago.id is None:
                cursor = await conn.execute(
                    "INSERT INTO pagos_semanales (miembro, monto, semana, descripcion, pagado, fecha_pago) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    valores,
                )
                return dataclasses.replace(pago, id=cursor.lastrowid)
            await conn.execute(
                "UPDATE pagos_semanales SET miembro = ?, monto = ?, semana = ?, descripcion = ?, "
                "pagado = ?, fecha_pago = ? WHERE id = ?",
                (*valores, pago.id),
            )
        return pago

    async def get_by_id(self, pago_id: int) -> PagoSemanal | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(f"SELECT {_COLUMNAS} FROM pagos_semanales WHERE id = ?", (pago_id,))
            fila = await cursor.fetchone()
        return None if fila is None else _a_pago(fila)

    async def delete(self, pago_id: int) -> None:
        async with self._db.sesion() as conn:
            await conn.execute("DELETE FROM pagos_semanales WHERE id = ?", (pago_id,))

    async def list(self, filtro: FiltroPagos = FiltroPagos()) -> list[PagoSemanal]:
        donde, parametros = clausula_where(
            [
                ("semana = ?", filtro.semana.isoformat() if filtro.semana else None),
                ("fecha_pago >= ?", a_texto_o_none(filtro.pagado_desde)),
                ("fecha_pago <= ?", a_texto_o_none(filtro.pagado_hasta)),
            ]
        )
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM pagos_semanales {donde} ORDER BY semana, miembro, id", parametros
            )
            filas = await cursor.fetchall()
        return [_a_pago(fila) for fila in filas]
