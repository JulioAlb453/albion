from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto


@dataclass(frozen=True)
class FiltroGastos:
    desde: datetime | None = None
    hasta: datetime | None = None
    categoria: CategoriaGasto | None = None


class IGastoRepository(ABC):
    @abstractmethod
    async def save(self, gasto: Gasto) -> Gasto: ...

    @abstractmethod
    async def save_many(self, gastos: list[Gasto]) -> list[Gasto]:
        """Importación por lotes (CSV). Todo o nada."""

    @abstractmethod
    async def get_by_id(self, gasto_id: int) -> Gasto | None: ...

    @abstractmethod
    async def list(self, filtro: FiltroGastos = FiltroGastos()) -> list[Gasto]: ...

    @abstractmethod
    async def delete(self, gasto_id: int) -> None: ...
