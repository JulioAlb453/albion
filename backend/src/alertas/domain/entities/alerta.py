from dataclasses import dataclass
from datetime import datetime

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta


@dataclass
class Alerta:
    seguimiento_id: int
    ciudad: Ciudad
    tipo: TipoVenta
    neto_unitario: int
    neto_referencia: int | None  # neto en la ciudad de referencia, si había dato
    motivo: str
    fecha: datetime
    id: int | None = None
