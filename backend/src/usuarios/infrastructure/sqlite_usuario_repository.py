from src.core.infrastructure.database import Database
from src.usuarios.domain.entities.usuario import Rol, Usuario
from src.usuarios.domain.ports.i_usuario_repository import IUsuarioRepository


class SqliteUsuarioRepository(IUsuarioRepository):
    """Guarda solo lo que el dominio conoce: ID de Discord, nombre, avatar y rol."""

    def __init__(self, db: Database):
        self._db = db

    async def get_by_discord_id(self, discord_id: str) -> Usuario | None:
        async with self._db.sesion() as conn:
            cursor = await conn.execute(
                "SELECT id, nombre, avatar_hash, rol FROM usuarios WHERE discord_id = ?",
                (discord_id,),
            )
            fila = await cursor.fetchone()
        if fila is None:
            return None
        id_, nombre, avatar_hash, rol = fila
        return Usuario(discord_id, nombre, avatar_hash, Rol(rol), id_)

    async def save(self, usuario: Usuario) -> Usuario:
        async with self._db.sesion() as conn:
            await conn.execute(
                "INSERT INTO usuarios (discord_id, nombre, avatar_hash, rol) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (discord_id) DO UPDATE SET "
                "nombre = excluded.nombre, avatar_hash = excluded.avatar_hash, rol = excluded.rol",
                (usuario.discord_id, usuario.nombre, usuario.avatar_hash, usuario.rol.value),
            )
            cursor = await conn.execute(
                "SELECT id FROM usuarios WHERE discord_id = ?", (usuario.discord_id,)
            )
            (usuario.id,) = await cursor.fetchone()
        return usuario
