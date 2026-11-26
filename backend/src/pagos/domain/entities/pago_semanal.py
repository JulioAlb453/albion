import dataclasses
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from src.core.domain.errors import ErrorDominio


def inicio_de_semana(dia: date) -> date:
    """El lunes de la semana del día (las semanas van de lunes a domingo, hora del servidor)."""
    return dia - timedelta(days=dia.weekday())


class EstadoPago(StrEnum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    PAGADO = "pagado"
    NO_RECLAMADO = "no_reclamado"  # terminó la semana sin cobrar todo: el resto queda en el gremio


@dataclass(frozen=True)
class PagoSemanal:
    """Plata asignada a un miembro para una semana. Solo lo pagado sale del saldo del gremio."""

    miembro: str
    monto: int  # lo asignado
    semana: date  # el lunes
    descripcion: str = ""
    pagado: int = 0
    fecha_pago: datetime | None = None  # la del último pago registrado
    id: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "miembro", self.miembro.strip())
        object.__setattr__(self, "descripcion", self.descripcion.strip())
        if not self.miembro:
            raise ErrorDominio("Falta el nombre del miembro")
        if self.monto <= 0:
            raise ErrorDominio("El monto asignado debe ser mayor a cero")
        if self.semana.weekday() != 0:
            raise ErrorDominio("La semana se identifica por su lunes")
        if not 0 <= self.pagado <= self.monto:
            raise ErrorDominio("Lo pagado no puede ser negativo ni pasar de lo asignado")
        if (self.pagado > 0) != (self.fecha_pago is not None):
            raise ErrorDominio("Un pago necesita su fecha, y sin pago no hay fecha")
        if self.fecha_pago is not None and not self.semana <= self.fecha_pago.date() <= self.fin_semana:
            raise ErrorDominio("El pago debe caer dentro de su semana (de lunes a domingo)")

    @property
    def fin_semana(self) -> date:
        return self.semana + timedelta(days=6)

    def registrar_pago(self, pagado: int, fecha: datetime) -> "PagoSemanal":
        """Fija el total pagado hasta ahora (sirve para corregir un pago parcial)."""
        if pagado > self.monto:
            raise ErrorDominio(f"No se puede pagar más de lo asignado ({self.monto})")
        return dataclasses.replace(self, pagado=pagado, fecha_pago=fecha if pagado > 0 else None)

    def estado(self, hoy: date) -> EstadoPago:
        if self.pagado >= self.monto:
            return EstadoPago.PAGADO
        if hoy > self.fin_semana:
            return EstadoPago.NO_RECLAMADO
        return EstadoPago.PARCIAL if self.pagado else EstadoPago.PENDIENTE

    def no_reclamado(self, hoy: date) -> int:
        return self.monto - self.pagado if self.estado(hoy) is EstadoPago.NO_RECLAMADO else 0
