from abc import ABC, abstractmethod

from src.alertas.domain.entities.seguimiento import Seguimiento


class ISeguimientoRepository(ABC):
    @abstractmethod
    async def save(self, seguimiento: Seguimiento) -> Seguimiento: ...

    @abstractmethod
    async def get_by_id(self, seguimiento_id: int) -> Seguimiento | None: ...

    @abstractmethod
    async def list_activos(self) -> list[Seguimiento]: ...

    @abstractmethod
    async def delete(self, seguimiento_id: int) -> None: ...
