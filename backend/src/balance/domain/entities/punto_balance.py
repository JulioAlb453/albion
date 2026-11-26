from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PuntoBalance:
    fecha: date
    ingresos: int  # ventas netas y otros ingresos del día
    gastos: int  # gastos y pagos semanales hechos ese día
    saldo: int     # saldo al cierre del día
