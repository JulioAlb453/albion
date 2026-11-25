from abc import ABC, abstractmethod
from collections.abc import Iterable

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.domain.entities.precio_mercado import PrecioMercado


class IProveedorPrecios(ABC):
    """Fuente externa de precios. La implementación real es la API del Albion Online Data Project."""

    @abstractmethod
    async def obtener_precios(
        self, objetos: Iterable[ObjetoRef], ciudades: Iterable[Ciudad]
    ) -> list[PrecioMercado]: ...
