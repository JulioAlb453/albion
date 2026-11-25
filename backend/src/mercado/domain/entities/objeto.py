from dataclasses import dataclass
from enum import StrEnum


class CategoriaObjeto(StrEnum):
    ARMA = "arma"
    ARMADURA = "armadura"
    ARTEFACTO = "artefacto"


@dataclass(frozen=True)
class Objeto:
    """Entrada del catálogo del juego. No tiene encantamiento ni calidad: eso es `ObjetoRef`."""

    base_id: str
    nombre: str  # nombre en español del catálogo del juego
    categoria: CategoriaObjeto

    @property
    def tiene_calidad(self) -> bool:
        # Los artefactos de crafteo no tienen calidad ni encantamiento.
        return self.categoria is not CategoriaObjeto.ARTEFACTO
