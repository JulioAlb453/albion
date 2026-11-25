from fastapi import APIRouter, Depends, Query

from src.alertas.infrastructure.http.esquemas import AlertaOut, SeguimientoIn, SeguimientoOut
from src.bootstrap.contenedor import Contenedor
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.usuarios.domain.entities.usuario import Usuario

router = APIRouter(prefix="/api", tags=["alertas"])


@router.post("/seguimientos", status_code=201)
async def crear_seguimiento(
    datos: SeguimientoIn,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> SeguimientoOut:
    seguimiento = await c.crear_seguimiento.ejecutar(
        usuario,
        ObjetoRef(datos.base_id, datos.encantamiento, datos.calidad),
        datos.ciudad_referencia,
        datos.porcentaje_minimo,
        datos.neto_minimo,
    )
    nombres = await c.obtener_nombres.ejecutar([seguimiento.objeto.base_id])
    return SeguimientoOut.desde(seguimiento, nombres)


@router.get("/seguimientos", dependencies=[Depends(usuario_actual)])
async def listar_seguimientos(c: Contenedor = Depends(contenedor)) -> list[SeguimientoOut]:
    seguimientos = await c.listar_seguimientos.ejecutar()
    nombres = await c.obtener_nombres.ejecutar(s.objeto.base_id for s in seguimientos)
    return [SeguimientoOut.desde(seguimiento, nombres) for seguimiento in seguimientos]


@router.delete("/seguimientos/{seguimiento_id}", status_code=204)
async def eliminar_seguimiento(
    seguimiento_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> None:
    await c.eliminar_seguimiento.ejecutar(usuario, seguimiento_id)


@router.get("/alertas", dependencies=[Depends(usuario_actual)])
async def listar_alertas(
    limite: int = Query(50, ge=1, le=200), c: Contenedor = Depends(contenedor)
) -> list[AlertaOut]:
    alertas = await c.listar_alertas.ejecutar(limite)
    nombres = await c.obtener_nombres.ejecutar(a.objeto.base_id for a in alertas)
    return [AlertaOut.desde(alerta, nombres) for alerta in alertas]
