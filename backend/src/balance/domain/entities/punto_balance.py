from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PuntoBalance:
    fecha: date
    ingresos: int  # ventas netas del día
    gastos: int
    saldo: int     # saldo al cierre del día
