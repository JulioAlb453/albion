from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

from src.pagos.domain.entities.pago_semanal import PagoSemanal


@dataclass(frozen=True)
class FiltroPagos:
    semana: date | None = None  # el lunes
    pagado_desde: datetime | None = None  # por fecha del pago: para el balance y los reportes
    pagado_hasta: datetime | None = None


class IPagoSemanalRepository(ABC):
    @abstractmethod
    async def save(self, pago: PagoSemanal) -> PagoSemanal:
        """Inserta uno nuevo (sin id) o reemplaza el que tiene ese id."""

    @abstractmethod
    async def get_by_id(self, pago_id: int) -> PagoSemanal | None: ...

    @abstractmethod
    async def list(self, filtro: FiltroPagos = FiltroPagos()) -> list[PagoSemanal]: ...

    @abstractmethod
    async def delete(self, pago_id: int) -> None: ...
