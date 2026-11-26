from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from src.ingresos.domain.entities.ingreso import CategoriaIngreso, Ingreso


@dataclass(frozen=True)
class FiltroIngresos:
    desde: datetime | None = None
    hasta: datetime | None = None
    categoria: CategoriaIngreso | None = None


class IIngresoRepository(ABC):
    @abstractmethod
    async def save(self, ingreso: Ingreso) -> Ingreso: ...

    @abstractmethod
    async def get_by_id(self, ingreso_id: int) -> Ingreso | None: ...

    @abstractmethod
    async def list(self, filtro: FiltroIngresos = FiltroIngresos()) -> list[Ingreso]: ...

    @abstractmethod
    async def delete(self, ingreso_id: int) -> None: ...
