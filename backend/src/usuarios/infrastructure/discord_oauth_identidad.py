from urllib.parse import urlencode

import httpx

from src.core.domain.errors import ServicioExternoNoDisponible, SesionInvalida
from src.core.infrastructure.http_externo import enviar
from src.usuarios.domain.entities.identidad import IdentidadDiscord
from src.usuarios.domain.ports.i_proveedor_identidad import IProveedorIdentidad

_AUTORIZAR = "https://discord.com/oauth2/authorize"


class DiscordOAuthIdentidad(IProveedorIdentidad):
    """OAuth2 de Discord con el permiso mínimo: `identify`.

    No se pide `email`, así que Discord no lo entrega. El token de acceso se usa una vez para
    leer el perfil y se revoca enseguida: no se guarda ni se reutiliza.
    """

    def __init__(
        self, cliente: httpx.AsyncClient, client_id: str, client_secret: str, redirect_uri: str
    ):
        self._cliente = cliente
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def url_autorizacion(self, estado: str) -> str:
        consulta = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "scope": "identify",
                "redirect_uri": self._redirect_uri,
                "state": estado,
                "prompt": "none",  # si ya aceptó antes, no vuelve a mostrar la pantalla
            }
        )
        return f"{_AUTORIZAR}?{consulta}"

    async def identificar(self, codigo: str) -> IdentidadDiscord:
        token = await self._canjear(codigo)
        try:
            perfil = await self._perfil(token)
        finally:
            await self._revocar(token)
        return IdentidadDiscord(
            discord_id=perfil["id"],
            nombre=perfil.get("global_name") or perfil["username"],
            avatar_hash=perfil.get("avatar"),
        )

    async def _canjear(self, codigo: str) -> str:
        respuesta = await enviar(
            self._cliente, "POST", "/oauth2/token", "Discord",
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "authorization_code",
                "code": codigo,
                "redirect_uri": self._redirect_uri,
            },
        )
        if respuesta.status_code == 400:  # código vencido, ya usado o inventado
            raise SesionInvalida("Discord rechazó el código de inicio de sesión")
        if respuesta.is_error:
            raise ServicioExternoNoDisponible(f"Discord respondió {respuesta.status_code} al iniciar sesión")
        return respuesta.json()["access_token"]

    async def _perfil(self, token: str) -> dict:
        respuesta = await enviar(
            self._cliente, "GET", "/users/@me", "Discord",
            headers={"Authorization": f"Bearer {token}"},
        )
        if respuesta.is_error:
            raise ServicioExternoNoDisponible(f"Discord respondió {respuesta.status_code} al leer el perfil")
        return respuesta.json()

    async def _revocar(self, token: str) -> None:
        """Mejor esfuerzo: si falla, el token vence solo y no impide entrar."""
        try:
            await enviar(
                self._cliente, "POST", "/oauth2/token/revoke", "Discord",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "token": token,
                    "token_type_hint": "access_token",
                },
            )
        except ServicioExternoNoDisponible:
            pass
