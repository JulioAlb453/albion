from collections.abc import Awaitable, Callable, Sequence

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from src.core.application.importacion import ErrorFila, ResultadoImportacion
from src.core.infrastructure.csv_utils import ErrorArchivo

LIMITE_BYTES = 2_000_000


def _rechazo(errores: Sequence[ErrorFila]) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "importadas": 0,
            "errores": [{"fila": e.fila, "mensaje": e.mensaje} for e in errores],
        },
    )


async def procesar_importacion[D](
    archivo: UploadFile,
    leer: Callable[[bytes], tuple[list[D], list[ErrorFila]]],
    importar: Callable[[list[D]], Awaitable[ResultadoImportacion]],
) -> JSONResponse:
    """Primero se lee todo el archivo, luego se valida con el dominio y solo entonces se guarda.
    Cualquier error rechaza el archivo completo y los informa todos con su número de fila (la 1
    es el encabezado)."""
    if archivo.size is not None and archivo.size > LIMITE_BYTES:
        return _rechazo([ErrorFila(1, "El archivo es demasiado grande (máximo 2 MB)")])
    try:
        filas, errores = leer(await archivo.read())
    except ErrorArchivo as error:
        return _rechazo([ErrorFila(1, str(error))])
    if errores:
        return _rechazo(errores)
    resultado = await importar(filas)
    if resultado.errores:
        return _rechazo(resultado.errores)
    return JSONResponse({"importadas": resultado.importadas, "errores": []})
