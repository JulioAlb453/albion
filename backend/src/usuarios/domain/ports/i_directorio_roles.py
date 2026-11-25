from abc import ABC, abstractmethod

from src.usuarios.domain.entities.usuario import Rol


class IDirectorioRoles(ABC):
    """Dice qué rol tiene una persona en el gremio. La implementación real consulta Discord."""

    @abstractmethod
    async def rol_de(self, discord_id: str) -> Rol | None:
        """`None` si la persona no tiene ningún rol del gremio: no puede entrar."""
