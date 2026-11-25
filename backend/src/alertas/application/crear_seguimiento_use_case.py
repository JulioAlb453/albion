from decimal import Decimal

from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.domain.ports.i_seguimiento_repository import ISeguimientoRepository
from src.core.domain.value_objects.ciudad import CIUDAD_PRINCIPAL, Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


class CrearSeguimiento:
    def __init__(self, seguimientos: ISeguimientoRepository):
        self._seguimientos = seguimientos

    async def ejecutar(
        self,
        actor: Usuario,
        objeto: ObjetoRef,
        ciudad_referencia: Ciudad = CIUDAD_PRINCIPAL,
        porcentaje_minimo: Decimal | None = None,
        neto_minimo: int | None = None,
    ) -> Seguimiento:
        exigir_admin(actor)
        seguimiento = Seguimiento(
            objeto, ciudad_referencia, porcentaje_minimo=porcentaje_minimo, neto_minimo=neto_minimo
        )
        return await self._seguimientos.save(seguimiento)
