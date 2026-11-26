from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.core.domain.errors import ErrorDominio


class CategoriaIngreso(StrEnum):
    """Plata que entra al gremio sin vender objetos."""

    DONACION = "donacion"
    TERRITORIOS = "territorios"  # territorios, temporada y recompensas del gremio
    BOTIN = "botin"  # bolsas de plata y plata del botín
    OTROS = "otros"


@dataclass
class Ingreso:
    categoria: CategoriaIngreso
    descripcion: str
    monto: int
    fecha: datetime
    id: int | None = None

    def __post_init__(self) -> None:
        self.descripcion = self.descripcion.strip()
        if self.monto <= 0:
            raise ErrorDominio("El monto del ingreso debe ser mayor a cero")
        if self.categoria is CategoriaIngreso.OTROS and not self.descripcion:
            raise ErrorDominio("Un ingreso de categoría 'otros' necesita descripción")
