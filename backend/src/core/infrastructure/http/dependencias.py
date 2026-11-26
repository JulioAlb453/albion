import hmac
from urllib.parse import unquote

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.bootstrap.contenedor import Contenedor
from src.core.domain.errors import SesionInvalida
from src.usuarios.domain.entities.usuario import Usuario

_esquema = HTTPBearer(auto_error=False)


def contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


async def _usuario_del_bot(request: Request, c: Contenedor) -> Usuario:
    """El bot de Discord actúa en nombre de quien usó el comando.

    Lleva una clave compartida y el ID de Discord de esa persona; su rol se consulta en Discord
    en cada petición, igual que en el inicio de sesión. La clave no vale si la petición llegó
    por internet: ngrok siempre agrega X-Forwarded-For, y el bot habla directo con la API.
    """
    clave = request.headers["x-bot-clave"]
    if not c.config.bot_clave or not hmac.compare_digest(clave.encode(), c.config.bot_clave.encode()):
        raise SesionInvalida("La clave del bot no es válida")
    if request.headers.get("x-forwarded-for"):
        raise SesionInvalida("La clave del bot solo vale dentro de la red interna")
    discord_id = request.headers.get("x-discord-id", "")
    if not (discord_id.isascii() and discord_id.isdigit()):
        raise SesionInvalida("Falta el ID de Discord de quien usó el comando")
    nombre = unquote(request.headers.get("x-discord-nombre", "")) or discord_id
    avatar = request.headers.get("x-discord-avatar") or None
    return await c.iniciar_sesion.ejecutar(discord_id, nombre, avatar)


async def usuario_actual(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
    c: Contenedor = Depends(contenedor),
) -> Usuario:
    """El usuario de la petición. Los permisos (admin o no) los exige cada caso de uso."""
    if "x-bot-clave" in request.headers:
        return await _usuario_del_bot(request, c)
    if credenciales is None:
        raise SesionInvalida("Falta iniciar sesión")
    discord_id = c.emisor_tokens.verificar_sesion(credenciales.credentials)
    usuario = await c.usuarios.get_by_discord_id(discord_id)
    if usuario is None:
        raise SesionInvalida("La sesión ya no es válida")
    return usuario
