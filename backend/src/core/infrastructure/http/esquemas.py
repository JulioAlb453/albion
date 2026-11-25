from collections.abc import Mapping

from pydantic import BaseModel

from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.objeto_ref import ObjetoRef


class ObjetoOut(BaseModel):
    """Cómo se muestra un objeto en cualquier respuesta. `nombre` es None si no está en el catálogo."""

    base_id: str
    nombre: str | None
    etiqueta: str  # notación de jugador: T6.2
    encantamiento: int
    calidad: Calidad


def objeto_out(objeto: ObjetoRef, nombres: Mapping[str, str]) -> ObjetoOut:
    return ObjetoOut(
        base_id=objeto.base_id,
        nombre=nombres.get(objeto.base_id),
        etiqueta=objeto.etiqueta,
        encantamiento=objeto.encantamiento,
        calidad=objeto.calidad,
    )
