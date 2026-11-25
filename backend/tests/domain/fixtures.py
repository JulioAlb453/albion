from datetime import UTC, datetime, timedelta

from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.mercado.domain.entities.precio_mercado import PrecioMercado

AHORA = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
ESPADA = ObjetoRef("T6_MAIN_SWORD", encantamiento=2, calidad=Calidad.SOBRESALIENTE)


def precio(
    ciudad: Ciudad,
    venta: int = 0,
    compra: int = 0,
    hace: timedelta = timedelta(minutes=30),
    objeto: ObjetoRef = ESPADA,
) -> PrecioMercado:
    fecha = AHORA - hace
    return PrecioMercado(
        objeto=objeto,
        ciudad=ciudad,
        venta_minima=venta,
        venta_minima_fecha=fecha if venta else None,
        compra_maxima=compra,
        compra_maxima_fecha=fecha if compra else None,
    )
