from abc import ABC, abstractmethod

from src.alertas.domain.entities.alerta import Alerta


class IAlertaRepository(ABC):
    @abstractmethod
    async def save(self, alerta: Alerta) -> Alerta: ...

    @abstractmethod
    async def ultima_de(self, seguimiento_id: int) -> Alerta | None:
        """Última alerta del seguimiento, para respetar el tiempo de espera."""

    @abstractmethod
    async def list_recientes(self, limite: int = 50) -> list[Alerta]: ...
