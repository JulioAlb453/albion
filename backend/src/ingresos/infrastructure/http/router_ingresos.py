from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.bootstrap.contenedor import Contenedor
from src.core.infrastructure.http.dependencias import contenedor, usuario_actual
from src.ingresos.application.casos_de_uso import DatosIngreso
from src.ingresos.domain.entities.ingreso import CategoriaIngreso, Ingreso
from src.ingresos.domain.ports.i_ingreso_repository import FiltroIngresos
from src.usuarios.domain.entities.usuario import Usuario

router = APIRouter(prefix="/api/ingresos", tags=["ingresos"])


class IngresoIn(BaseModel):
    categoria: CategoriaIngreso
    descripcion: str = ""
    monto: int = Field(gt=0)
    fecha: datetime | None = None  # sin fecha se usa la hora actual


class IngresoOut(BaseModel):
    id: int
    categoria: CategoriaIngreso
    descripcion: str
    monto: int
    fecha: datetime

    @classmethod
    def desde(cls, i: Ingreso) -> "IngresoOut":
        return cls(id=i.id, categoria=i.categoria, descripcion=i.descripcion, monto=i.monto, fecha=i.fecha)


def filtro_ingresos(
    desde: datetime | None = None, hasta: datetime | None = None, categoria: CategoriaIngreso | None = None
) -> FiltroIngresos:
    return FiltroIngresos(desde=desde, hasta=hasta, categoria=categoria)


@router.post("", status_code=201)
async def registrar(
    datos: IngresoIn, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> IngresoOut:
    nuevo = DatosIngreso(datos.categoria, datos.descripcion, datos.monto, datos.fecha)
    return IngresoOut.desde(await c.registrar_ingreso.ejecutar(usuario, nuevo))


@router.get("", dependencies=[Depends(usuario_actual)])
async def listar(
    filtro: FiltroIngresos = Depends(filtro_ingresos), c: Contenedor = Depends(contenedor)
) -> list[IngresoOut]:
    return [IngresoOut.desde(i) for i in await c.listar_ingresos.ejecutar(filtro)]


@router.delete("/{ingreso_id}", status_code=204)
async def eliminar(
    ingreso_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> None:
    await c.eliminar_ingreso.ejecutar(usuario, ingreso_id)
