from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.balance.domain.ports.i_saldo_inicial_repository import ISaldoInicialRepository
from src.core.domain.errors import EntidadNoEncontrada


class ObtenerSaldoInicial:
    def __init__(self, saldos: ISaldoInicialRepository):
        self._saldos = saldos

    async def ejecutar(self) -> SaldoInicial:
        saldo = await self._saldos.get()
        if saldo is None:
            raise EntidadNoEncontrada("Falta configurar el saldo inicial")
        return saldo
