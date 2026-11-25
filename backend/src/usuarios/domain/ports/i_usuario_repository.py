from abc import ABC, abstractmethod

from src.usuarios.domain.entities.usuario import Usuario


class IUsuarioRepository(ABC):
    @abstractmethod
    async def get_by_discord_id(self, discord_id: str) -> Usuario | None: ...

    @abstractmethod
    async def save(self, usuario: Usuario) -> Usuario:
        """Crea o actualiza por `discord_id` (el nombre y avatar cambian en Discord)."""
