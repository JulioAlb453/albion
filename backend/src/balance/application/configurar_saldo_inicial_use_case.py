from datetime import date

from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.balance.domain.ports.i_saldo_inicial_repository import ISaldoInicialRepository
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


class ConfigurarSaldoInicial:
    def __init__(self, saldos: ISaldoInicialRepository):
        self._saldos = saldos

    async def ejecutar(self, actor: Usuario, monto: int, fecha: date) -> SaldoInicial:
        exigir_admin(actor)
        return await self._saldos.save(SaldoInicial(monto, fecha))
