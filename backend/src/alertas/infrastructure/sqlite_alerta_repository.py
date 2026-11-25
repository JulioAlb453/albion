from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.ports.i_alerta_repository import IAlertaRepository
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto, desde_texto

_COLUMNAS = "id, seguimiento_id, ciudad, tipo, neto_unitario, neto_referencia, motivo, fecha"


def _a_alerta(fila: tuple) -> Alerta:
    id_, seguimiento_id, ciudad, tipo, neto_unitario, neto_referencia, motivo, fecha = fila
    return Alerta(
        seguimiento_id=seguimiento_id,
        ciudad=Ciudad(ciudad),
        tipo=TipoVenta(tipo),
        neto_unitario=neto_unitario,
        neto_referencia=neto_referencia,
        motivo=motivo,
        fecha=desde_texto(fecha),
        id=id_,
    )


class SqliteAlertaRepository(IAlertaRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save(self, alerta: Alerta) -> Alerta:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                "INSERT INTO alertas (seguimiento_id, ciudad, tipo, neto_unitario, "
                "neto_referencia, motivo, fecha) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    alerta.seguimiento_id, alerta.ciudad.value, alerta.tipo.value,
                    alerta.neto_unitario, alerta.neto_referencia, alerta.motivo,
                    a_texto(alerta.fecha),
                ),
            )
            alerta.id = cursor.lastrowid
        return alerta

    async def ultima_de(self, seguimiento_id: int) -> Alerta | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM alertas WHERE seguimiento_id = ? "
                "ORDER BY fecha DESC, id DESC LIMIT 1",
                (seguimiento_id,),
            )
            fila = await cursor.fetchone()
        return None if fila is None else _a_alerta(fila)

    async def list_recientes(self, limite: int = 50) -> list[Alerta]:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM alertas ORDER BY fecha DESC, id DESC LIMIT ?", (limite,)
            )
            filas = await cursor.fetchall()
        return [_a_alerta(fila) for fila in filas]
