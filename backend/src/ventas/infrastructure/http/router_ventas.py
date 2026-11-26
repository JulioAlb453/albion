from datetime import datetime

from fastapi import APIRouter, Depends, Response, UploadFile
from fastapi.responses import JSONResponse

from src.bootstrap.contenedor import Contenedor
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.core.infrastructure.exportacion import Formato, descarga
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.core.infrastructure.http.importacion import procesar_importacion
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin
from src.ventas.domain.entities.venta import Venta
from src.ventas.domain.ports.i_venta_repository import FiltroVentas
from src.ventas.infrastructure.csv_ventas import leer_ventas, plantilla_ventas
from src.ventas.infrastructure.http import exportacion
from src.ventas.infrastructure.http.esquemas import CorreccionVentaIn, VentaIn, VentaOut

router = APIRouter(prefix="/api/ventas", tags=["ventas"])


def filtro_ventas(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    ciudad: Ciudad | None = None,
    tipo: TipoVenta | None = None,
    base_id: str | None = None,
) -> FiltroVentas:
    return FiltroVentas(desde=desde, hasta=hasta, ciudad=ciudad, tipo=tipo, base_id=base_id)


async def a_salidas(c: Contenedor, ventas: list[Venta]) -> list[VentaOut]:
    nombres = await c.obtener_nombres.ejecutar(v.objeto.base_id for v in ventas)
    return [VentaOut.desde(venta, nombres) for venta in ventas]


@router.post("", status_code=201)
async def registrar(
    datos: VentaIn, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> VentaOut:
    venta = await c.registrar_venta.ejecutar(usuario, datos.a_dominio())
    return (await a_salidas(c, [venta]))[0]


@router.get("", dependencies=[Depends(usuario_actual)])
async def listar(
    filtro: FiltroVentas = Depends(filtro_ventas), c: Contenedor = Depends(contenedor)
) -> list[VentaOut]:
    return await a_salidas(c, await c.listar_ventas.ejecutar(filtro))


@router.get("/exportar", dependencies=[Depends(usuario_actual)])
async def exportar(
    formato: Formato = "csv",
    filtro: FiltroVentas = Depends(filtro_ventas),
    c: Contenedor = Depends(contenedor),
) -> Response:
    """Descarga las ventas que cumplen el filtro, en CSV o Excel."""
    ventas = await a_salidas(c, await c.listar_ventas.ejecutar(filtro))
    nombre = f"ventas-{c.reloj.ahora():%Y-%m-%d}"
    return descarga(formato, nombre, {"Ventas": (exportacion.ENCABEZADOS, exportacion.filas(ventas))})


@router.get("/plantilla", dependencies=[Depends(usuario_actual)])
async def plantilla() -> Response:
    """CSV de ejemplo con las columnas que acepta la importación."""
    return Response(
        plantilla_ventas(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla-ventas.csv"'},
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
        archivo, leer_ventas, lambda filas: c.importar_ventas.ejecutar(usuario, filas, fila_inicial=2)
    )


@router.patch("/{venta_id}")
async def corregir(
    venta_id: int,
    datos: CorreccionVentaIn,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> VentaOut:
    venta = await c.corregir_venta.ejecutar(
        usuario, venta_id, encantamiento=datos.encantamiento, calidad=datos.calidad
    )
    return (await a_salidas(c, [venta]))[0]


@router.delete("/{venta_id}", status_code=204)
async def eliminar(
    venta_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> None:
    await c.eliminar_venta.ejecutar(usuario, venta_id)
