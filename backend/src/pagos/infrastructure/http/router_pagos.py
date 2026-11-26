from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.bootstrap.contenedor import Contenedor
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.pagos.application.casos_de_uso import DatosAsignacion
from src.pagos.domain.entities.pago_semanal import EstadoPago, PagoSemanal
from src.usuarios.domain.entities.usuario import Usuario

router = APIRouter(prefix="/api/pagos-semanales", tags=["pagos semanales"])


class AsignacionIn(BaseModel):
    miembro: str
    monto: int = Field(gt=0)
    semana: date | None = None  # cualquier día de la semana; sin él, la semana actual
    descripcion: str = ""


class PagoIn(BaseModel):
    pagado: int = Field(ge=0)  # el total pagado hasta ahora, no lo que se suma
    fecha_pago: datetime | None = None  # sin fecha se usa la hora actual


class PagoSemanalOut(BaseModel):
    id: int
    miembro: str
    monto: int
    descripcion: str
    semana: date
    fin_semana: date
    pagado: int
    fecha_pago: datetime | None
    estado: EstadoPago
    no_reclamado: int  # lo que se queda el gremio porque la semana terminó sin cobrarlo

    @classmethod
    def desde(cls, p: PagoSemanal, hoy: date) -> "PagoSemanalOut":
        return cls(
            id=p.id, miembro=p.miembro, monto=p.monto, descripcion=p.descripcion, semana=p.semana,
            fin_semana=p.fin_semana, pagado=p.pagado, fecha_pago=p.fecha_pago, estado=p.estado(hoy),
            no_reclamado=p.no_reclamado(hoy),
        )


@router.post("", status_code=201)
async def asignar(
    datos: AsignacionIn, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> PagoSemanalOut:
    nuevo = DatosAsignacion(datos.miembro, datos.monto, datos.semana, datos.descripcion)
    return PagoSemanalOut.desde(await c.asignar_pago.ejecutar(usuario, nuevo), c.reloj.ahora().date())


@router.get("", dependencies=[Depends(usuario_actual)])
async def listar(semana: date | None = None, c: Contenedor = Depends(contenedor)) -> list[PagoSemanalOut]:
    """Los de la semana que contiene ese día, o todos."""
    hoy = c.reloj.ahora().date()
    return [PagoSemanalOut.desde(p, hoy) for p in await c.listar_pagos.ejecutar(semana)]


@router.patch("/{pago_id}")
async def registrar_pago(
    pago_id: int, datos: PagoIn, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> PagoSemanalOut:
    pago = await c.registrar_pago.ejecutar(usuario, pago_id, datos.pagado, datos.fecha_pago)
    return PagoSemanalOut.desde(pago, c.reloj.ahora().date())


@router.delete("/{pago_id}", status_code=204)
async def eliminar(
    pago_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> None:
    await c.eliminar_pago.ejecutar(usuario, pago_id)
