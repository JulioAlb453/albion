from abc import ABC, abstractmethod

from src.usuarios.domain.entities.identidad import IdentidadDiscord


class IProveedorIdentidad(ABC):
    """Verifica quién es una persona. La implementación real es el OAuth2 de Discord."""

    @abstractmethod
    def url_autorizacion(self, estado: str) -> str:
        """Dirección a la que se manda a la persona para que acepte; `estado` evita falsificaciones."""

    @abstractmethod
    async def identificar(self, codigo: str) -> IdentidadDiscord:
        """Cambia el código de autorización por la identidad. Lanza `SesionInvalida` si no vale."""
