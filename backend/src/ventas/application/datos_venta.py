from dataclasses import dataclass
from datetime import datetime

from src.core.application.fechas import a_utc
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.ventas.domain.entities.venta import Venta


@dataclass(frozen=True)
class DatosVenta:
    """Lo que llega de fuera (formulario, bot, CSV) ya convertido a tipos del dominio."""

    objeto: ObjetoRef
    ciudad: Ciudad
    tipo: TipoVenta
    cantidad: int
    precio_unitario: int
    fecha: datetime | None = None  # None: se usa la hora actual
    tarifa_extra: int = 0


def construir_venta(datos: DatosVenta, ahora: datetime) -> Venta:
    return Venta.registrar(
        objeto=datos.objeto,
        ciudad=datos.ciudad,
        tipo=datos.tipo,
        cantidad=datos.cantidad,
        precio_unitario=datos.precio_unitario,
        fecha=a_utc(datos.fecha or ahora),
        tarifa_extra=datos.tarifa_extra,
    )
