from dataclasses import dataclass
from enum import StrEnum


class Rol(StrEnum):
    ADMIN = "admin"      # registra ventas y gastos, configura alertas
    GENERAL = "general"  # solo consulta y exporta


@dataclass
class Usuario:
    """Identidad mínima obtenida de Discord con el scope `identify`.

    No hay campo de correo ni de token por diseño: el sistema no los pide ni los guarda.
    """

    discord_id: str
    nombre: str
    avatar_hash: str | None
    rol: Rol
    id: int | None = None

    @property
    def puede_registrar(self) -> bool:
        return self.rol is Rol.ADMIN
