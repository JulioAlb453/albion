import httpx

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.ports.i_notificador_alertas import INotificadorAlertas
from src.core.domain.errors import ServicioExternoNoDisponible
from src.core.infrastructure.http_externo import enviar
from src.mercado.domain.ports.i_catalogo_objetos import ICatalogoObjetos


class NotificadorDiscordWebhook(INotificadorAlertas):
    """Publica cada alerta en un canal de Discord mediante un webhook (no hace falta el bot)."""

    def __init__(self, cliente: httpx.AsyncClient, url_webhook: str, catalogo: ICatalogoObjetos):
        self._cliente = cliente
        self._url = url_webhook
        self._catalogo = catalogo

    async def notificar(self, alerta: Alerta) -> None:
        objeto = await self._catalogo.get_by_base_id(alerta.objeto.base_id)
        nombre = objeto.nombre if objeto else alerta.objeto.base_id
        calidad = alerta.objeto.calidad.name.replace("_", " ").capitalize()
        lineas = [
            f"🔔 **{nombre}** ({alerta.objeto.etiqueta}, {calidad})",
            alerta.motivo,
            f"Neto por unidad: **{alerta.neto_unitario:,}** en {alerta.ciudad.value} ({alerta.tipo.value})",
        ]
        if alerta.neto_referencia is not None:
            lineas.append(f"Referencia: {alerta.neto_referencia:,}")
        respuesta = await enviar(
            self._cliente, "POST", self._url, "Discord",
            # `parse: []` evita que un @everyone dentro del texto avise a todo el servidor.
            json={"content": "\n".join(lineas), "allowed_mentions": {"parse": []}},
        )
        if respuesta.is_error:
            raise ServicioExternoNoDisponible(
                f"Discord respondió {respuesta.status_code} al publicar la alerta"
            )
