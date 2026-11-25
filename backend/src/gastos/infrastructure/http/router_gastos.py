from datetime import datetime

from fastapi import APIRouter, Depends, Response, UploadFile
from fastapi.responses import JSONResponse

from src.bootstrap.contenedor import Contenedor
from src.core.infrastructure.exportacion import Formato, descarga
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.core.infrastructure.http.importacion import procesar_importacion
from src.gastos.domain.entities.gasto import CategoriaGasto
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos
from src.gastos.infrastructure.csv_gastos import leer_gastos, plantilla_gastos
from src.gastos.infrastructure.http import exportacion
from src.gastos.infrastructure.http.esquemas import GastoIn, GastoOut
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin

router = APIRouter(prefix="/api/gastos", tags=["gastos"])


def filtro_gastos(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    categoria: CategoriaGasto | None = None,
) -> FiltroGastos:
    return FiltroGastos(desde=desde, hasta=hasta, categoria=categoria)


@router.post("", status_code=201)
async def registrar(
    datos: GastoIn, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> GastoOut:
    return GastoOut.desde(await c.registrar_gasto.ejecutar(usuario, datos.a_dominio()))


@router.get("", dependencies=[Depends(usuario_actual)])
async def listar(
    filtro: FiltroGastos = Depends(filtro_gastos), c: Contenedor = Depends(contenedor)
) -> list[GastoOut]:
    return [GastoOut.desde(gasto) for gasto in await c.listar_gastos.ejecutar(filtro)]


@router.get("/exportar", dependencies=[Depends(usuario_actual)])
async def exportar(
    formato: Formato = "csv",
    filtro: FiltroGastos = Depends(filtro_gastos),
    c: Contenedor = Depends(contenedor),
) -> Response:
    """Descarga los gastos que cumplen el filtro, en CSV o Excel."""
    gastos = [GastoOut.desde(gasto) for gasto in await c.listar_gastos.ejecutar(filtro)]
    nombre = f"gastos-{c.reloj.ahora():%Y-%m-%d}"
    return descarga(formato, nombre, {"Gastos": (exportacion.ENCABEZADOS, exportacion.filas(gastos))})


@router.get("/plantilla", dependencies=[Depends(usuario_actual)])
async def plantilla() -> Response:
    """CSV de ejemplo con las columnas que acepta la importación."""
    return Response(
        plantilla_gastos(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla-gastos.csv"'},
    )


@router.post("/importar")
async def importar(
    archivo: UploadFile,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> JSONResponse:
    """Importa un CSV completo o nada. Si algo falla, informa todas las filas malas."""
    exigir_admin(usuario)  # antes de leer el archivo
    return await procesar_importacion(
        archivo, leer_gastos, lambda filas: c.importar_gastos.ejecutar(usuario, filas, fila_inicial=2)
    )


@router.delete("/{gasto_id}", status_code=204)
async def eliminar(
    gasto_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> None:
    await c.eliminar_gasto.ejecutar(usuario, gasto_id)
