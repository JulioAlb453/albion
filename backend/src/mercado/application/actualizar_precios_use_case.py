from collections.abc import Iterable

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.domain.entities.precio_mercado import PrecioMercado
from src.mercado.domain.ports.i_precio_mercado_repository import IPrecioMercadoRepository
from src.mercado.domain.ports.i_proveedor_precios import IProveedorPrecios

CIUDADES_MERCADO = tuple(Ciudad)


class ActualizarPrecios:
    """Trae precios de la API y reemplaza los guardados. Una sola consulta por lote."""

    def __init__(self, proveedor: IProveedorPrecios, precios: IPrecioMercadoRepository):
        self._proveedor = proveedor
        self._precios = precios

    async def ejecutar(
        self, objetos: Iterable[ObjetoRef], ciudades: Iterable[Ciudad] = CIUDADES_MERCADO
    ) -> list[PrecioMercado]:
        unicos = list(dict.fromkeys(objetos))
        if not unicos:
            return []
        obtenidos = await self._proveedor.obtener_precios(unicos, ciudades)
        await self._precios.save_many(obtenidos)
        return obtenidos
