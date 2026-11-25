from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.core.domain.errors import ErrorDominio


class CategoriaGasto(StrEnum):
    COMPRA_EQUIPO = "compra_equipo"
    REPARACIONES = "reparaciones"
    REEQUIPAMIENTO_BUILDS = "reequipamiento_builds"
    INGREDIENTES_COMIDA = "ingredientes_comida"
    OTROS = "otros"


@dataclass
class Gasto:
    categoria: CategoriaGasto
    descripcion: str
    monto: int
    fecha: datetime
    id: int | None = None

    @classmethod
    def registrar(
        cls, *, categoria: CategoriaGasto, descripcion: str, monto: int, fecha: datetime
    ) -> "Gasto":
        descripcion = descripcion.strip()
        if monto <= 0:
            raise ErrorDominio("El monto del gasto debe ser mayor a cero")
        if categoria is CategoriaGasto.OTROS and not descripcion:
            raise ErrorDominio("Un gasto de categoría 'otros' necesita descripción")
        return cls(categoria, descripcion, monto, fecha)
