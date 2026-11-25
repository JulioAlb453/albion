from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.entities.seguimiento import Seguimiento
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import CIUDAD_PRINCIPAL, Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.http.esquemas import ObjetoOut, objeto_out


class SeguimientoIn(BaseModel):
    base_id: str
    encantamiento: int = Field(0, ge=0, le=4)
    calidad: Calidad = Calidad.NORMAL
    ciudad_referencia: Ciudad = CIUDAD_PRINCIPAL
    porcentaje_minimo: Decimal | None = Field(None, gt=0)  # otra ciudad paga este % más neto
    neto_minimo: int | None = Field(None, gt=0)  # el neto unitario alcanza este valor


class SeguimientoOut(BaseModel):
    id: int
    objeto: ObjetoOut
    ciudad_referencia: Ciudad
    porcentaje_minimo: float | None
    neto_minimo: int | None

    @classmethod
    def desde(cls, seguimiento: Seguimiento, nombres: Mapping[str, str]) -> "SeguimientoOut":
        porcentaje = seguimiento.porcentaje_minimo
        return cls(
            id=seguimiento.id,
            objeto=objeto_out(seguimiento.objeto, nombres),
            ciudad_referencia=seguimiento.ciudad_referencia,
            porcentaje_minimo=None if porcentaje is None else float(porcentaje),
            neto_minimo=seguimiento.neto_minimo,
        )


class AlertaOut(BaseModel):
    id: int
    seguimiento_id: int
    objeto: ObjetoOut
    ciudad: Ciudad
    tipo: TipoVenta
    neto_unitario: int
    neto_referencia: int | None
    motivo: str
    fecha: datetime

    @classmethod
    def desde(cls, alerta: Alerta, nombres: Mapping[str, str]) -> "AlertaOut":
        return cls(
            id=alerta.id,
            seguimiento_id=alerta.seguimiento_id,
            objeto=objeto_out(alerta.objeto, nombres),
            ciudad=alerta.ciudad,
            tipo=alerta.tipo,
            neto_unitario=alerta.neto_unitario,
            neto_referencia=alerta.neto_referencia,
            motivo=alerta.motivo,
            fecha=alerta.fecha,
        )
