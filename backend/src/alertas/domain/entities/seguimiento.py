from dataclasses import dataclass
from decimal import Decimal

from src.core.domain.errors import ErrorDominio
from src.core.domain.value_objects.ciudad import CIUDAD_PRINCIPAL, Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef


@dataclass
class Seguimiento:
    """Objeto vigilado. Dispara alerta si se cumple cualquiera de los criterios definidos.

    - `porcentaje_minimo`: otra ciudad paga ese porcentaje más neto que la de referencia.
    - `neto_minimo`: el neto unitario en alguna ciudad alcanza ese valor.
    """

    objeto: ObjetoRef
    ciudad_referencia: Ciudad = CIUDAD_PRINCIPAL
    porcentaje_minimo: Decimal | None = None
    neto_minimo: int | None = None
    activo: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        if self.porcentaje_minimo is None and self.neto_minimo is None:
            raise ErrorDominio("El seguimiento necesita al menos un criterio de alerta")
        if self.porcentaje_minimo is not None and self.porcentaje_minimo <= 0:
            raise ErrorDominio("El porcentaje mínimo debe ser mayor a cero")
        if self.neto_minimo is not None and self.neto_minimo <= 0:
            raise ErrorDominio("El neto mínimo debe ser mayor a cero")
