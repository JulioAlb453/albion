from dataclasses import dataclass
from datetime import date

from src.core.domain.errors import ErrorDominio


@dataclass
class SaldoInicial:
    """Plata del gremio en la fecha en que empieza el registro. Es único."""

    monto: int
    fecha: date

    def __post_init__(self) -> None:
        if self.monto < 0:
            raise ErrorDominio("El saldo inicial no puede ser negativo")
