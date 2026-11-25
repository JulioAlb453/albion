from src.core.domain.errors import AccesoDenegado
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.ports.i_directorio_roles import IDirectorioRoles
from src.usuarios.domain.ports.i_usuario_repository import IUsuarioRepository


class IniciarSesion:
    """Recibe la identidad que Discord ya verificó y decide si entra y con qué rol.

    El rol se consulta en cada inicio de sesión: si alguien pierde su rol en el servidor,
    deja de entrar. Emitir el token de sesión es cosa de la infraestructura.
    """

    def __init__(self, usuarios: IUsuarioRepository, directorio: IDirectorioRoles):
        self._usuarios = usuarios
        self._directorio = directorio

    async def ejecutar(
        self, discord_id: str, nombre: str, avatar_hash: str | None
    ) -> Usuario:
        rol = await self._directorio.rol_de(discord_id)
        if rol is None:
            raise AccesoDenegado("No tienes un rol del gremio")
        return await self._usuarios.save(Usuario(discord_id, nombre, avatar_hash, rol))
