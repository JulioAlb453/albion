from src.core.domain.services.calculadora_impuestos import DesgloseVenta
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto, a_texto_o_none, desde_texto
from src.core.infrastructure.sql import clausula_where
from src.ventas.domain.entities.venta import Venta
from src.ventas.domain.ports.i_venta_repository import FiltroVentas, IVentaRepository

_COLUMNAS = (
    "id, base_id, encantamiento, calidad, ciudad, tipo, cantidad, precio_unitario, "
    "fecha, bruto, impuesto, tarifa_publicacion, neto"
)


def _a_venta(fila: tuple) -> Venta:
    (id_, base_id, encantamiento, calidad, ciudad, tipo, cantidad, precio_unitario,
     fecha, bruto, impuesto, tarifa_publicacion, neto) = fila
    return Venta(
        objeto=ObjetoRef(base_id, encantamiento, Calidad(calidad)),
        ciudad=Ciudad(ciudad),
        tipo=TipoVenta(tipo),
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        fecha=desde_texto(fecha),
        desglose=DesgloseVenta(bruto, impuesto, tarifa_publicacion, neto),
        id=id_,
    )


async def _insertar(conn, venta: Venta) -> int:
    cursor = await conn.execute(
        "INSERT INTO ventas (base_id, encantamiento, calidad, ciudad, tipo, cantidad, "
        "precio_unitario, fecha, bruto, impuesto, tarifa_publicacion, neto) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            venta.objeto.base_id, venta.objeto.encantamiento, int(venta.objeto.calidad),
            venta.ciudad.value, venta.tipo.value, venta.cantidad, venta.precio_unitario,
            a_texto(venta.fecha), venta.desglose.bruto, venta.desglose.impuesto,
            venta.desglose.tarifa_publicacion, venta.desglose.neto,
        ),
    )
    return cursor.lastrowid


class SqliteVentaRepository(IVentaRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save(self, venta: Venta) -> Venta:
        async with self._db.sesion() as conn:
            venta.id = await _insertar(conn, venta)
        return venta

    async def save_many(self, ventas: list[Venta]) -> list[Venta]:
        async with self._db.sesion() as conn:
            ids = [await _insertar(conn, venta) for venta in ventas]
        # Los ids se asignan al final: si el lote se deshace, ninguna venta queda con uno ajeno.
        for venta, id_ in zip(ventas, ids):
            venta.id = id_
        return ventas

    async def get_by_id(self, venta_id: int) -> Venta | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(f"SELECT {_COLUMNAS} FROM ventas WHERE id = ?", (venta_id,))
            fila = await cursor.fetchone()
        return None if fila is None else _a_venta(fila)

    async def delete(self, venta_id: int) -> None:
        async with self._db.sesion() as conn:
            await conn.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))

    async def list(self, filtro: FiltroVentas = FiltroVentas()) -> list[Venta]:
        donde, parametros = clausula_where(
            [
                ("fecha >= ?", a_texto_o_none(filtro.desde)),
                ("fecha <= ?", a_texto_o_none(filtro.hasta)),
                ("ciudad = ?", filtro.ciudad and filtro.ciudad.value),
                ("tipo = ?", filtro.tipo and filtro.tipo.value),
                ("base_id = ?", filtro.base_id),
            ]
        )
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                f"SELECT {_COLUMNAS} FROM ventas {donde} ORDER BY fecha, id", parametros
            )
            filas = await cursor.fetchall()
        return [_a_venta(fila) for fila in filas]
