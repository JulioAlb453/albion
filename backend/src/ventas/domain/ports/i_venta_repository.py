from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.ventas.domain.entities.venta import Venta


@dataclass(frozen=True)
class FiltroVentas:
    desde: datetime | None = None
    hasta: datetime | None = None
    ciudad: Ciudad | None = None
    tipo: TipoVenta | None = None
    base_id: str | None = None


class IVentaRepository(ABC):
    @abstractmethod
    async def save(self, venta: Venta) -> Venta: ...

    @abstractmethod
    async def save_many(self, ventas: list[Venta]) -> list[Venta]:
        """Importación por lotes (CSV). Todo o nada."""

    @abstractmethod
    async def get_by_id(self, venta_id: int) -> Venta | None: ...

    @abstractmethod
    async def list(self, filtro: FiltroVentas = FiltroVentas()) -> list[Venta]: ...

    @abstractmethod
    async def delete(self, venta_id: int) -> None: ...

    @abstractmethod
    async def update(self, venta: Venta) -> Venta:
        """Reemplaza los datos de una venta que ya existe (la de `venta.id`)."""
