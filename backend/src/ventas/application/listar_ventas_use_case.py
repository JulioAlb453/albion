from dataclasses import replace

from src.core.application.fechas import a_utc_o_none
from src.ventas.domain.entities.venta import Venta
from src.ventas.domain.ports.i_venta_repository import FiltroVentas, IVentaRepository


class ListarVentas:
    def __init__(self, ventas: IVentaRepository):
        self._ventas = ventas

    async def ejecutar(self, filtro: FiltroVentas = FiltroVentas()) -> list[Venta]:
        utc = replace(filtro, desde=a_utc_o_none(filtro.desde), hasta=a_utc_o_none(filtro.hasta))
        return await self._ventas.list(utc)
