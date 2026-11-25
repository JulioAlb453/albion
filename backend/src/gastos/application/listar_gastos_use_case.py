from dataclasses import replace

from src.core.application.fechas import a_utc_o_none
from src.gastos.domain.entities.gasto import Gasto
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos, IGastoRepository


class ListarGastos:
    def __init__(self, gastos: IGastoRepository):
        self._gastos = gastos

    async def ejecutar(self, filtro: FiltroGastos = FiltroGastos()) -> list[Gasto]:
        utc = replace(filtro, desde=a_utc_o_none(filtro.desde), hasta=a_utc_o_none(filtro.hasta))
        return await self._gastos.list(utc)
