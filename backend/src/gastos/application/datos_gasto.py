from dataclasses import dataclass
from datetime import datetime

from src.core.application.fechas import a_utc
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto


@dataclass(frozen=True)
class DatosGasto:
    categoria: CategoriaGasto
    descripcion: str
    monto: int
    fecha: datetime | None = None  # None: se usa la hora actual


def construir_gasto(datos: DatosGasto, ahora: datetime) -> Gasto:
    return Gasto(datos.categoria, datos.descripcion, datos.monto, a_utc(datos.fecha or ahora))
