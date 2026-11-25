from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.bootstrap.contenedor import Contenedor
from src.core.domain.errors import SesionInvalida
from src.usuarios.domain.entities.usuario import Usuario

_esquema = HTTPBearer(auto_error=False)


def contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


async def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema),
    c: Contenedor = Depends(contenedor),
) -> Usuario:
    """El usuario de la petición. Los permisos (admin o no) los exige cada caso de uso."""
    if credenciales is None:
        raise SesionInvalida("Falta iniciar sesión")
    discord_id = c.emisor_tokens.verificar_sesion(credenciales.credentials)
    usuario = await c.usuarios.get_by_discord_id(discord_id)
    if usuario is None:
        raise SesionInvalida("La sesión ya no es válida")
    return usuario
