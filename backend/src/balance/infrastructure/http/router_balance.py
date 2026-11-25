from datetime import date, datetime

from fastapi import APIRouter, Depends, Response

from src.balance.infrastructure.http import exportacion
from src.balance.infrastructure.http.esquemas import (
    PuntoBalanceOut,
    ReportesOut,
    SaldoInicialIO,
)
from src.bootstrap.contenedor import Contenedor
from src.core.infrastructure.exportacion import Formato, descarga
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.usuarios.domain.entities.usuario import Usuario

router = APIRouter(prefix="/api", tags=["balance"])


@router.get("/balance/saldo-inicial", dependencies=[Depends(usuario_actual)])
async def obtener_saldo_inicial(c: Contenedor = Depends(contenedor)) -> SaldoInicialIO:
    saldo = await c.obtener_saldo_inicial.ejecutar()
    return SaldoInicialIO(monto=saldo.monto, fecha=saldo.fecha)


@router.put("/balance/saldo-inicial")
async def configurar_saldo_inicial(
    datos: SaldoInicialIO,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> SaldoInicialIO:
    saldo = await c.configurar_saldo_inicial.ejecutar(usuario, datos.monto, datos.fecha)
    return SaldoInicialIO(monto=saldo.monto, fecha=saldo.fecha)


@router.get("/balance/evolucion", dependencies=[Depends(usuario_actual)])
async def evolucion(
    hasta: date | None = None, c: Contenedor = Depends(contenedor)
) -> list[PuntoBalanceOut]:
    """Saldo al cierre de cada día desde el saldo inicial; sin `hasta`, llega hasta hoy."""
    return [PuntoBalanceOut.desde(punto) for punto in await c.obtener_evolucion.ejecutar(hasta)]


@router.get("/reportes", dependencies=[Depends(usuario_actual)])
async def reportes(
    desde: datetime | None = None,
    hasta: datetime | None = None,
    c: Contenedor = Depends(contenedor),
) -> ReportesOut:
    return await _reportes(c, desde, hasta)


@router.get("/reportes/exportar", dependencies=[Depends(usuario_actual)])
async def exportar_reportes(
    formato: Formato = "csv",
    desde: datetime | None = None,
    hasta: datetime | None = None,
    c: Contenedor = Depends(contenedor),
) -> Response:
    """Excel lleva una hoja por tabla; CSV lleva solo la ganancia por objeto."""
    reportes_ = await _reportes(c, desde, hasta)
    return descarga(formato, f"reportes-{c.reloj.ahora():%Y-%m-%d}", exportacion.hojas(reportes_))


async def _reportes(c: Contenedor, desde: datetime | None, hasta: datetime | None) -> ReportesOut:
    resumen = await c.obtener_reportes.ejecutar(desde, hasta)
    nombres = await c.obtener_nombres.ejecutar(g.objeto.base_id for g in resumen.ganancia_por_objeto)
    return ReportesOut.desde(resumen, nombres)
