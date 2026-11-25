from collections.abc import Iterable

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.infrastructure.database import Database
from src.core.infrastructure.fechas_sql import a_texto_o_none, desde_texto_o_none
from src.mercado.domain.entities.precio_mercado import PrecioMercado
from src.mercado.domain.ports.i_precio_mercado_repository import IPrecioMercadoRepository


class SqlitePrecioMercadoRepository(IPrecioMercadoRepository):
    def __init__(self, db: Database):
        self._db = db

    async def save_many(self, precios: list[PrecioMercado]) -> None:
        filas = [
            (
                p.objeto.base_id, p.objeto.encantamiento, int(p.objeto.calidad), p.ciudad.value,
                p.venta_minima, a_texto_o_none(p.venta_minima_fecha),
                p.compra_maxima, a_texto_o_none(p.compra_maxima_fecha),
            )
            for p in precios
        ]
        async with self._db.sesion() as conn:
            await conn.executemany(
                "INSERT INTO precios_mercado (base_id, encantamiento, calidad, ciudad, "
                "venta_minima, venta_minima_fecha, compra_maxima, compra_maxima_fecha) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT (base_id, encantamiento, calidad, ciudad) DO UPDATE SET "
                "venta_minima = excluded.venta_minima, "
                "venta_minima_fecha = excluded.venta_minima_fecha, "
                "compra_maxima = excluded.compra_maxima, "
                "compra_maxima_fecha = excluded.compra_maxima_fecha",
                filas,
            )

    async def get(self, objeto: ObjetoRef, ciudades: Iterable[Ciudad]) -> list[PrecioMercado]:
        nombres = [ciudad.value for ciudad in ciudades]
        if not nombres:
            return []
        marcas = ", ".join("?" * len(nombres))
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                "SELECT ciudad, venta_minima, venta_minima_fecha, compra_maxima, compra_maxima_fecha "
                "FROM precios_mercado WHERE base_id = ? AND encantamiento = ? AND calidad = ? "
                f"AND ciudad IN ({marcas}) ORDER BY ciudad",
                (objeto.base_id, objeto.encantamiento, int(objeto.calidad), *nombres),
            )
            filas = await cursor.fetchall()
        return [
            PrecioMercado(
                objeto=objeto,
                ciudad=Ciudad(ciudad),
                venta_minima=venta_minima,
                venta_minima_fecha=desde_texto_o_none(venta_fecha),
                compra_maxima=compra_maxima,
                compra_maxima_fecha=desde_texto_o_none(compra_fecha),
            )
            for ciudad, venta_minima, venta_fecha, compra_maxima, compra_fecha in filas
        ]
