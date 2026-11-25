from collections.abc import Sequence

from src.core.domain.ports.i_reloj import IReloj
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.application.actualizar_precios_use_case import CIUDADES_MERCADO, ActualizarPrecios
from src.mercado.domain.ports.i_precio_mercado_repository import IPrecioMercadoRepository
from src.mercado.domain.services.comparador_ventas import comparar_por_ciudad
from src.mercado.domain.value_objects.opcion_venta import ComparacionCiudad


class CompararPrecios:
    """Lee de la caché local. Solo consulta la API si no hay ningún dato del objeto."""

    def __init__(
        self, precios: IPrecioMercadoRepository, actualizar: ActualizarPrecios, reloj: IReloj
    ):
        self._precios = precios
        self._actualizar = actualizar
        self._reloj = reloj

    async def ejecutar(
        self,
        objeto: ObjetoRef,
        cantidad: int = 1,
        ciudades: Sequence[Ciudad] = CIUDADES_MERCADO,
    ) -> list[ComparacionCiudad]:
        guardados = await self._precios.get(objeto, ciudades)
        if not guardados:
            guardados = await self._actualizar.ejecutar([objeto], ciudades)
        return comparar_por_ciudad(guardados, ahora=self._reloj.ahora(), cantidad=cantidad)
