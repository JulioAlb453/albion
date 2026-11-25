from dataclasses import dataclass, field
from datetime import datetime

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.domain.ports.i_alerta_repository import IAlertaRepository
from src.alertas.domain.ports.i_notificador_alertas import INotificadorAlertas
from src.alertas.domain.ports.i_seguimiento_repository import ISeguimientoRepository
from src.alertas.domain.services.evaluador_alertas import evaluar
from src.core.domain.ports.i_reloj import IReloj
from src.mercado.application.actualizar_precios_use_case import CIUDADES_MERCADO, ActualizarPrecios
from src.mercado.domain.ports.i_precio_mercado_repository import IPrecioMercadoRepository
from src.mercado.domain.services.comparador_ventas import comparar_por_ciudad


@dataclass
class ResultadoRevision:
    alertas: list[Alerta] = field(default_factory=list)  # las que se guardaron en esta revisión
    errores: list[str] = field(default_factory=list)


class RevisarAlertas:
    """Tarea periódica: refresca los precios y avisa de los seguimientos que cumplen su criterio.

    Si falla la consulta a la API la revisión entera falla (el planificador la reintenta en el
    siguiente ciclo). Si falla un seguimiento suelto, o su aviso, se anota en `errores` y se
    sigue con los demás; una alerta ya guardada no se pierde porque el aviso falle.
    """

    def __init__(
        self,
        seguimientos: ISeguimientoRepository,
        alertas: IAlertaRepository,
        precios: IPrecioMercadoRepository,
        actualizar: ActualizarPrecios,
        notificador: INotificadorAlertas,
        reloj: IReloj,
    ):
        self._seguimientos = seguimientos
        self._alertas = alertas
        self._precios = precios
        self._actualizar = actualizar
        self._notificador = notificador
        self._reloj = reloj

    async def ejecutar(self) -> ResultadoRevision:
        activos = await self._seguimientos.list_activos()
        resultado = ResultadoRevision()
        if not activos:
            return resultado
        await self._actualizar.ejecutar([s.objeto for s in activos])
        ahora = self._reloj.ahora()
        for seguimiento in activos:
            try:
                await self._revisar(seguimiento, ahora, resultado)
            except Exception as error:  # un seguimiento con falla no debe frenar a los demás
                resultado.errores.append(f"Seguimiento {seguimiento.id}: {error}")
        return resultado

    async def _revisar(
        self, seguimiento: Seguimiento, ahora: datetime, resultado: ResultadoRevision
    ) -> None:
        precios = await self._precios.get(seguimiento.objeto, CIUDADES_MERCADO)
        alerta = evaluar(
            seguimiento,
            comparar_por_ciudad(precios, ahora=ahora),
            ultima_alerta=await self._alertas.ultima_de(seguimiento.id),
            ahora=ahora,
        )
        if alerta is None:
            return
        guardada = await self._alertas.save(alerta)
        resultado.alertas.append(guardada)
        await self._notificador.notificar(guardada)
