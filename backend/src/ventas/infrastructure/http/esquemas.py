from collections.abc import Mapping
from datetime import datetime

from pydantic import BaseModel, Field

from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.http.esquemas import ObjetoOut, objeto_out
from src.ventas.application.datos_venta import DatosVenta
from src.ventas.domain.entities.venta import Venta


class CorreccionVentaIn(BaseModel):
    """Lo que se puede corregir de una venta ya registrada."""

    encantamiento: int = Field(ge=0, le=4)
    calidad: Calidad


class VentaIn(BaseModel):
    base_id: str
    encantamiento: int = Field(0, ge=0, le=4)
    calidad: Calidad = Calidad.NORMAL
    ciudad: Ciudad
    tipo: TipoVenta
    cantidad: int = Field(gt=0)
    precio_unitario: int = Field(gt=0)
    fecha: datetime | None = None  # sin fecha se usa la hora actual
    tarifa_extra: int = Field(0, ge=0)  # lo pagado al reajustar una orden ya publicada

    def a_dominio(self) -> DatosVenta:
        return DatosVenta(
            objeto=ObjetoRef(self.base_id, self.encantamiento, self.calidad),
            ciudad=self.ciudad,
            tipo=self.tipo,
            cantidad=self.cantidad,
            precio_unitario=self.precio_unitario,
            fecha=self.fecha,
            tarifa_extra=self.tarifa_extra,
        )


class VentaOut(BaseModel):
    id: int
    objeto: ObjetoOut
    ciudad: Ciudad
    tipo: TipoVenta
    cantidad: int
    precio_unitario: int
    fecha: datetime
    bruto: int
    impuesto: int
    tarifa_publicacion: int
    neto: int

    @classmethod
    def desde(cls, venta: Venta, nombres: Mapping[str, str]) -> "VentaOut":
        return cls(
            id=venta.id,
            objeto=objeto_out(venta.objeto, nombres),
            ciudad=venta.ciudad,
            tipo=venta.tipo,
            cantidad=venta.cantidad,
            precio_unitario=venta.precio_unitario,
            fecha=venta.fecha,
            bruto=venta.desglose.bruto,
            impuesto=venta.desglose.impuesto,
            tarifa_publicacion=venta.desglose.tarifa_publicacion,
            neto=venta.desglose.neto,
        )
