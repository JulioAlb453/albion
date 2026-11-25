from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field

from src.core.domain.errors import ErrorDominio


@dataclass(frozen=True)
class ErrorFila:
    fila: int
    mensaje: str


@dataclass(frozen=True)
class ResultadoImportacion:
    importadas: int
    errores: list[ErrorFila] = field(default_factory=list)


async def importar[D, E](
    filas: Iterable[D],
    construir: Callable[[D], E],
    guardar_lote: Callable[[list[E]], Awaitable[object]],
    fila_inicial: int = 1,
) -> ResultadoImportacion:
    """Todo o nada: si una sola fila es inválida no se guarda ninguna y se informan todas las malas."""
    entidades: list[E] = []
    errores: list[ErrorFila] = []
    for numero, fila in enumerate(filas, start=fila_inicial):
        try:
            entidades.append(construir(fila))
        except ErrorDominio as error:
            errores.append(ErrorFila(numero, str(error)))
    if errores:
        return ResultadoImportacion(0, errores)
    if entidades:
        await guardar_lote(entidades)
    return ResultadoImportacion(len(entidades))
