import re
from dataclasses import dataclass

from src.core.domain.errors import ErrorDominio
from src.core.domain.value_objects.calidad import Calidad

_API_ID = re.compile(r"^(T(\d)_[A-Z0-9_]+?)(?:@(\d))?$")


@dataclass(frozen=True)
class ObjetoRef:
    """Identifica un objeto concreto del mercado: tipo, encantamiento y calidad.

    `base_id` es el identificador de Albion sin encantamiento, p. ej. `T6_MAIN_SWORD`.
    """

    base_id: str
    encantamiento: int = 0
    calidad: Calidad = Calidad.NORMAL

    def __post_init__(self) -> None:
        coincidencia = _API_ID.match(self.base_id)
        if coincidencia is None or coincidencia.group(3) is not None:
            raise ErrorDominio(f"Identificador de objeto inválido: {self.base_id!r}")
        if not 1 <= self.tier <= 8:
            raise ErrorDominio(f"Tier fuera de rango: {self.tier}")
        if not 0 <= self.encantamiento <= 4:
            raise ErrorDominio(f"Encantamiento fuera de rango: {self.encantamiento}")

    @property
    def tier(self) -> int:
        return int(self.base_id[1])

    @property
    def api_id(self) -> str:
        """Identificador que espera la API: `T6_MAIN_SWORD@2`."""
        return f"{self.base_id}@{self.encantamiento}" if self.encantamiento else self.base_id

    @property
    def etiqueta(self) -> str:
        """Notación de jugador: `T6.2`."""
        return f"T{self.tier}.{self.encantamiento}"

    @classmethod
    def desde_api_id(cls, item_id: str, calidad: Calidad = Calidad.NORMAL) -> "ObjetoRef":
        coincidencia = _API_ID.match(item_id)
        if coincidencia is None:
            raise ErrorDominio(f"Identificador de objeto inválido: {item_id!r}")
        encantamiento = int(coincidencia.group(3) or 0)
        return cls(coincidencia.group(1), encantamiento, calidad)
