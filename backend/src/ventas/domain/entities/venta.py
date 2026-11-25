from dataclasses import dataclass
from datetime import datetime

from src.core.domain.errors import ErrorDominio
from src.core.domain.services.calculadora_impuestos import (
    TASAS_PREMIUM,
    DesgloseVenta,
    TasasMercado,
    calcular_desglose,
)
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta


@dataclass
class Venta:
    objeto: ObjetoRef
    ciudad: Ciudad
    tipo: TipoVenta
    cantidad: int
    precio_unitario: int
    fecha: datetime
    desglose: DesgloseVenta
    id: int | None = None

    @classmethod
    def registrar(
        cls,
        *,
        objeto: ObjetoRef,
        ciudad: Ciudad,
        tipo: TipoVenta,
        cantidad: int,
        precio_unitario: int,
        fecha: datetime,
        tasas: TasasMercado = TASAS_PREMIUM,
        tarifa_extra: int = 0,
    ) -> "Venta":
        if tipo is TipoVenta.ORDEN and not ciudad.admite_orden_venta:
            raise ErrorDominio(f"{ciudad} no admite órdenes de venta, solo venta directa")
        desglose = calcular_desglose(precio_unitario, cantidad, tipo, tasas, tarifa_extra)
        return cls(objeto, ciudad, tipo, cantidad, precio_unitario, fecha, desglose)
