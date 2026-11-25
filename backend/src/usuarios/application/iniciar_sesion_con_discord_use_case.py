from src.usuarios.application.iniciar_sesion_use_case import IniciarSesion
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.ports.i_proveedor_identidad import IProveedorIdentidad


class IniciarSesionConDiscord:
    """Cierra el flujo de OAuth: del código que devuelve Discord a un usuario con rol."""

    def __init__(self, identidad: IProveedorIdentidad, iniciar_sesion: IniciarSesion):
        self._identidad = identidad
        self._iniciar_sesion = iniciar_sesion

    async def ejecutar(self, codigo: str) -> Usuario:
        persona = await self._identidad.identificar(codigo)
        return await self._iniciar_sesion.ejecutar(
            persona.discord_id, persona.nombre, persona.avatar_hash
        )
