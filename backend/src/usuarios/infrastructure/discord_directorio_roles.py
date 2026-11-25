import httpx

from src.core.domain.errors import ServicioExternoNoDisponible
from src.core.infrastructure.http_externo import enviar
from src.usuarios.domain.entities.usuario import Rol
from src.usuarios.domain.ports.i_directorio_roles import IDirectorioRoles

_MIEMBRO_DESCONOCIDO = 10007  # código de Discord: ese usuario no está en el servidor


class DirectorioRolesDiscord(IDirectorioRoles):
    """El rol dentro del gremio sale de los roles del servidor de Discord, consultados con el bot."""

    def __init__(
        self,
        cliente: httpx.AsyncClient,
        bot_token: str,
        guild_id: str,
        rol_admin_id: str,
        rol_general_id: str,
    ):
        self._cliente = cliente
        self._bot_token = bot_token
        self._guild_id = guild_id
        self._rol_admin_id = rol_admin_id
        self._rol_general_id = rol_general_id

    async def rol_de(self, discord_id: str) -> Rol | None:
        respuesta = await enviar(
            self._cliente, "GET", f"/guilds/{self._guild_id}/members/{discord_id}", "Discord",
            headers={"Authorization": f"Bot {self._bot_token}"},
        )
        if respuesta.status_code == 404:
            if _codigo(respuesta) == _MIEMBRO_DESCONOCIDO:
                return None
            raise ServicioExternoNoDisponible(
                "Discord no encontró el servidor: revisa GREMIO_DISCORD_GUILD_ID"
            )
        if respuesta.is_error:
            raise ServicioExternoNoDisponible(
                f"Discord respondió {respuesta.status_code} al consultar los roles"
            )
        roles = set(respuesta.json().get("roles", []))
        if self._rol_admin_id in roles:
            return Rol.ADMIN
        if self._rol_general_id in roles:
            return Rol.GENERAL
        return None


def _codigo(respuesta: httpx.Response) -> int | None:
    try:
        return respuesta.json().get("code")
    except ValueError:
        return None
