from abc import ABC, abstractmethod
from collections.abc import Iterable

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.domain.entities.precio_mercado import PrecioMercado


class IPrecioMercadoRepository(ABC):
    """Caché local de precios, para no consultar la API en cada petición."""

    @abstractmethod
    async def save_many(self, precios: list[PrecioMercado]) -> None:
        """Reemplaza el precio guardado de cada (objeto, ciudad)."""

    @abstractmethod
    async def get(self, objeto: ObjetoRef, ciudades: Iterable[Ciudad]) -> list[PrecioMercado]: ...
