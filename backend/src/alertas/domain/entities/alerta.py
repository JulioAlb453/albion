from dataclasses import dataclass
from datetime import datetime

from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta


@dataclass
class Alerta:
    """Aviso ya emitido. Guarda el objeto: es lo que se vio en ese momento, aunque el
    seguimiento cambie después."""

    seguimiento_id: int
    objeto: ObjetoRef
    ciudad: Ciudad
    tipo: TipoVenta
    neto_unitario: int
    neto_referencia: int | None  # neto en la ciudad de referencia, si había dato
    motivo: str
    fecha: datetime
    id: int | None = None
