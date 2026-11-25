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

    def __post_init__(self) -> None:
        if self.tipo is TipoVenta.ORDEN and not self.ciudad.admite_orden_venta:
            raise ErrorDominio(f"{self.ciudad} no admite órdenes de venta, solo venta directa")
        if self.cantidad <= 0 or self.precio_unitario <= 0:
            raise ErrorDominio("La cantidad y el precio unitario deben ser mayores a cero")
        if self.desglose.bruto != self.precio_unitario * self.cantidad:
            raise ErrorDominio("El desglose no corresponde al precio y la cantidad")
        if self.tipo is TipoVenta.DIRECTA and self.desglose.tarifa_publicacion:
            raise ErrorDominio("La venta directa no paga tarifa de publicación")

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
        desglose = calcular_desglose(precio_unitario, cantidad, tipo, tasas, tarifa_extra)
        return cls(objeto, ciudad, tipo, cantidad, precio_unitario, fecha, desglose)
