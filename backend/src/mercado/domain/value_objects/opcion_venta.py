from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.domain.services.calculadora_impuestos import DesgloseVenta
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta


@dataclass(frozen=True)
class OpcionVenta:
    objeto: ObjetoRef
    ciudad: Ciudad
    tipo: TipoVenta
    precio_unitario: int
    cantidad: int
    desglose: DesgloseVenta
    fecha_dato: datetime
    antiguedad: timedelta
    confiable: bool  # False si el dato es más viejo que el límite configurado

    @property
    def neto_unitario(self) -> int:
        return self.desglose.neto // self.cantidad


@dataclass(frozen=True)
class ComparacionCiudad:
    """Directa contra orden en una misma ciudad. Cualquiera puede faltar por falta de datos."""

    ciudad: Ciudad
    directa: OpcionVenta | None
    orden: OpcionVenta | None

    @property
    def mejor(self) -> OpcionVenta | None:
        """La de mayor neto, pero un dato viejo nunca le gana a uno reciente: puede estar desactualizado."""
        candidatas = [o for o in (self.directa, self.orden) if o is not None]
        return max(candidatas, key=lambda o: (o.confiable, o.desglose.neto), default=None)

    @property
    def confiable(self) -> bool:
        mejor = self.mejor
        return mejor is not None and mejor.confiable

    @property
    def diferencia_orden_vs_directa(self) -> int | None:
        """Plata neta de más (o de menos) que deja la orden frente a vender directo."""
        if self.directa is None or self.orden is None:
            return None
        return self.orden.desglose.neto - self.directa.desglose.neto
