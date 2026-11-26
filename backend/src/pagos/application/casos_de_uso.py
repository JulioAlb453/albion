from dataclasses import dataclass
from datetime import date, datetime

from src.core.application.fechas import a_utc
from src.core.domain.errors import EntidadNoEncontrada
from src.core.domain.ports.i_reloj import IReloj
from src.pagos.domain.entities.pago_semanal import PagoSemanal, inicio_de_semana
from src.pagos.domain.ports.i_pago_semanal_repository import FiltroPagos, IPagoSemanalRepository
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


@dataclass(frozen=True)
class DatosAsignacion:
    miembro: str
    monto: int
    semana: date | None = None  # cualquier día de la semana; None: la actual
    descripcion: str = ""


class AsignarPagoSemanal:
    def __init__(self, pagos: IPagoSemanalRepository, reloj: IReloj):
        self._pagos = pagos
        self._reloj = reloj

    async def ejecutar(self, actor: Usuario, datos: DatosAsignacion) -> PagoSemanal:
        exigir_admin(actor)
        lunes = inicio_de_semana(datos.semana or self._reloj.ahora().date())
        return await self._pagos.save(PagoSemanal(datos.miembro, datos.monto, lunes, datos.descripcion))


class RegistrarPagoSemanal:
    """Fija cuánto se le ha pagado al miembro. Sirve también para corregir un pago parcial."""

    def __init__(self, pagos: IPagoSemanalRepository, reloj: IReloj):
        self._pagos = pagos
        self._reloj = reloj

    async def ejecutar(
        self, actor: Usuario, pago_id: int, pagado: int, fecha: datetime | None = None
    ) -> PagoSemanal:
        exigir_admin(actor)
        pago = await self._pagos.get_by_id(pago_id)
        if pago is None:
            raise EntidadNoEncontrada(f"No existe el pago semanal {pago_id}")
        return await self._pagos.save(pago.registrar_pago(pagado, a_utc(fecha or self._reloj.ahora())))


class ListarPagosSemanales:
    def __init__(self, pagos: IPagoSemanalRepository):
        self._pagos = pagos

    async def ejecutar(self, dia: date | None = None) -> list[PagoSemanal]:
        """Los de la semana de ese día, o todos."""
        return await self._pagos.list(FiltroPagos(semana=inicio_de_semana(dia) if dia else None))


class EliminarPagoSemanal:
    def __init__(self, pagos: IPagoSemanalRepository):
        self._pagos = pagos

    async def ejecutar(self, actor: Usuario, pago_id: int) -> None:
        exigir_admin(actor)
        if await self._pagos.get_by_id(pago_id) is None:
            raise EntidadNoEncontrada(f"No existe el pago semanal {pago_id}")
        await self._pagos.delete(pago_id)
