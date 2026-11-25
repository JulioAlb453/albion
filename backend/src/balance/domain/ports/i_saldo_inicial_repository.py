from abc import ABC, abstractmethod

from src.balance.domain.entities.saldo_inicial import SaldoInicial


class ISaldoInicialRepository(ABC):
    @abstractmethod
    async def get(self) -> SaldoInicial | None: ...

    @abstractmethod
    async def save(self, saldo: SaldoInicial) -> SaldoInicial: ...
