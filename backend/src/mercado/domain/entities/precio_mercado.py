from dataclasses import dataclass
from datetime import datetime

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef


@dataclass(frozen=True)
class PrecioMercado:
    """Foto del mercado de un objeto en una ciudad, tal como la reportan los jugadores.

    Un precio 0 significa que no hay órdenes registradas: no es un precio real.
    """

    objeto: ObjetoRef
    ciudad: Ciudad
    venta_minima: int                     # orden de venta más barata (sell_price_min)
    venta_minima_fecha: datetime | None
    compra_maxima: int                    # orden de compra más alta (buy_price_max)
    compra_maxima_fecha: datetime | None

    @property
    def tiene_orden_venta(self) -> bool:
        return self.venta_minima > 0 and self.venta_minima_fecha is not None

    @property
    def tiene_orden_compra(self) -> bool:
        return self.compra_maxima > 0 and self.compra_maxima_fecha is not None
