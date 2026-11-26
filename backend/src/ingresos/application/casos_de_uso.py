from dataclasses import dataclass, replace
from datetime import datetime

from src.core.application.fechas import a_utc, a_utc_o_none
from src.core.domain.errors import EntidadNoEncontrada
from src.core.domain.ports.i_reloj import IReloj
from src.ingresos.domain.entities.ingreso import CategoriaIngreso, Ingreso
from src.ingresos.domain.ports.i_ingreso_repository import FiltroIngresos, IIngresoRepository
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


@dataclass(frozen=True)
class DatosIngreso:
    categoria: CategoriaIngreso
    descripcion: str
    monto: int
    fecha: datetime | None = None  # None: se usa la hora actual


class RegistrarIngreso:
    def __init__(self, ingresos: IIngresoRepository, reloj: IReloj):
        self._ingresos = ingresos
        self._reloj = reloj

    async def ejecutar(self, actor: Usuario, datos: DatosIngreso) -> Ingreso:
        exigir_admin(actor)
        fecha = a_utc(datos.fecha or self._reloj.ahora())
        return await self._ingresos.save(Ingreso(datos.categoria, datos.descripcion, datos.monto, fecha))


class ListarIngresos:
    def __init__(self, ingresos: IIngresoRepository):
        self._ingresos = ingresos

    async def ejecutar(self, filtro: FiltroIngresos = FiltroIngresos()) -> list[Ingreso]:
        utc = replace(filtro, desde=a_utc_o_none(filtro.desde), hasta=a_utc_o_none(filtro.hasta))
        return await self._ingresos.list(utc)


class EliminarIngreso:
    def __init__(self, ingresos: IIngresoRepository):
        self._ingresos = ingresos

    async def ejecutar(self, actor: Usuario, ingreso_id: int) -> None:
        exigir_admin(actor)
        if await self._ingresos.get_by_id(ingreso_id) is None:
            raise EntidadNoEncontrada(f"No existe el ingreso {ingreso_id}")
        await self._ingresos.delete(ingreso_id)
