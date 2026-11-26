from dataclasses import dataclass
from enum import StrEnum


class CategoriaObjeto(StrEnum):
    """Las secciones del mercado del juego, con nombres del gremio."""

    ARMA = "arma"              # armas y manos secundarias
    ARMADURA = "armadura"      # armaduras, cascos y zapatos
    CAPA = "capa"
    BOLSA = "bolsa"
    MONTURA = "montura"
    CONSUMIBLE = "consumible"  # comida, pociones y tomos de conocimiento
    RECURSO = "recurso"        # materias primas y refinadas
    ARTEFACTO = "artefacto"
    RECOLECCION = "recoleccion"  # herramientas y equipo de recolección
    GRANJA = "granja"
    MOBILIARIO = "mobiliario"
    APARIENCIA = "apariencia"
    OTRO = "otro"


# Lo típico de cada categoría, para cuando no se sabe más del objeto.
_CON_CALIDAD = {CategoriaObjeto.ARMA, CategoriaObjeto.ARMADURA, CategoriaObjeto.CAPA, CategoriaObjeto.BOLSA}


@dataclass(frozen=True)
class Objeto:
    """Entrada del catálogo del juego. El encantamiento y la calidad de una venta van en `ObjetoRef`;
    aquí solo está qué admite el objeto.

    `encantamiento_min`/`max`: el rango que se puede elegir. Un recurso encantado es otro objeto
    del juego (T4_ORE_LEVEL2) con su encantamiento fijo, así que su rango es 2..2.
    """

    base_id: str
    nombre: str  # nombre en español del catálogo del juego
    categoria: CategoriaObjeto
    tiene_calidad: bool | None = None
    encantamiento_min: int = 0
    encantamiento_max: int | None = None

    def __post_init__(self) -> None:
        tipica = self.categoria in _CON_CALIDAD
        if self.tiene_calidad is None:
            object.__setattr__(self, "tiene_calidad", tipica)
        if self.encantamiento_max is None:
            object.__setattr__(self, "encantamiento_max", 4 if tipica else self.encantamiento_min)
