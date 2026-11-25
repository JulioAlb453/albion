from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.domain.errors import (
    AccesoDenegado,
    EntidadNoEncontrada,
    ErrorDominio,
    ServicioExternoNoDisponible,
    SesionInvalida,
)


def _respuesta(codigo: int, error: Exception, encabezados: dict[str, str] | None = None):
    return JSONResponse(status_code=codigo, content={"detail": str(error)}, headers=encabezados)


def registrar_manejadores(app: FastAPI) -> None:
    """Cada error del sistema tiene su código HTTP. Starlette elige el manejador más específico."""

    @app.exception_handler(EntidadNoEncontrada)
    async def no_encontrada(_: Request, error: EntidadNoEncontrada):
        return _respuesta(404, error)

    @app.exception_handler(AccesoDenegado)
    async def acceso_denegado(_: Request, error: AccesoDenegado):
        return _respuesta(403, error)

    @app.exception_handler(ErrorDominio)
    async def regla_violada(_: Request, error: ErrorDominio):
        return _respuesta(422, error)

    @app.exception_handler(SesionInvalida)
    async def sesion_invalida(_: Request, error: SesionInvalida):
        return _respuesta(401, error, {"WWW-Authenticate": "Bearer"})

    @app.exception_handler(ServicioExternoNoDisponible)
    async def servicio_externo(_: Request, error: ServicioExternoNoDisponible):
        return _respuesta(502, error)
