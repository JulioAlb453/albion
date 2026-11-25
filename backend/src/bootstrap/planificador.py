import asyncio
import logging
from collections.abc import Awaitable, Callable

_registro = logging.getLogger("gremio.planificador")


def _registrar_error(error: Exception) -> None:
    _registro.error("La tarea periódica falló: %s", error, exc_info=error)


async def ejecutar_periodicamente(
    tarea: Callable[[], Awaitable[object]],
    intervalo_segundos: float,
    detener: asyncio.Event,
    ante_error: Callable[[Exception], None] = _registrar_error,
) -> None:
    """Corre la tarea al arrancar y luego cada intervalo, hasta que se active `detener`.

    Una falla de la tarea se informa y el ciclo sigue: la API de Albion puede caerse un rato
    y la siguiente revisión debe intentarlo de nuevo. Al detenerse no espera el intervalo.
    """
    while not detener.is_set():
        try:
            await tarea()
        except Exception as error:  # la tarea es lo único que puede fallar aquí
            ante_error(error)
        try:
            await asyncio.wait_for(detener.wait(), timeout=intervalo_segundos)
        except TimeoutError:
            pass
